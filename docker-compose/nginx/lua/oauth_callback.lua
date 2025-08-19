-- oauth_callback.lua - OAuth callback handler
local http = require "resty.http"
local redis = require "resty.redis"
local json = require "cjson"
local str = require "resty.string"

-- Extract provider from state or determine from context
local args = ngx.req.get_uri_args()
local code = args.code
local state = args.state
local error_param = args.error

-- For now, assume Google since that's what we're configuring
-- In a full implementation, you could encode the provider in the state
local provider = "google"

ngx.log(ngx.INFO, "OAuth callback for provider: ", provider)

-- Check for OAuth error
if error_param then
    ngx.log(ngx.ERR, "OAuth error from provider ", provider, ": ", error_param)
    return ngx.redirect("/login.html?error=oauth_" .. error_param)
end

if not code or not state then
    ngx.log(ngx.ERR, "Missing code or state in OAuth callback")
    return ngx.redirect("/login.html?error=missing_params")
end

-- Validate state parameter
local oauth_states = ngx.shared.oauth_states
local stored_provider = oauth_states:get(state)
if not stored_provider or stored_provider ~= provider then
    ngx.log(ngx.ERR, "Invalid OAuth state for provider: ", provider)
    return ngx.redirect("/login.html?error=invalid_state")
end
oauth_states:delete(state)

-- OAuth provider token endpoints and user info
local token_configs = {
    google = {
        token_url = "https://oauth2.googleapis.com/token",
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    },
    github = {
        token_url = "https://github.com/login/oauth/access_token",
        user_info_url = "https://api.github.com/user"
    },
    microsoft = {
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        user_info_url = "https://graph.microsoft.com/v1.0/me"
    },
    apple = {
        token_url = "https://appleid.apple.com/auth/token",
        user_info_url = nil -- Apple provides user info in ID token
    }
}

local config = token_configs[provider]
if not config then
    ngx.log(ngx.ERR, "Unknown provider in callback: ", provider)
    return ngx.redirect("/login.html?error=unknown_provider")
end

-- Get credentials from global config
local oauth_creds = _G.OAUTH_CONFIG and _G.OAUTH_CONFIG[provider]
if not oauth_creds or not oauth_creds.client_id or not oauth_creds.client_secret then
    ngx.log(ngx.ERR, "Missing OAuth credentials for provider: ", provider)
    return ngx.redirect("/login.html?error=config_missing")
end

-- Exchange code for access token
local httpc = http:new()
httpc:set_timeout(10000) -- 10 second timeout

local redirect_uri = ngx.var.scheme .. "://" .. ngx.var.host .. "/auth/callback"

local token_res, err = httpc:request_uri(config.token_url, {
    method = "POST",
    body = ngx.encode_args({
        client_id = oauth_creds.client_id,
        client_secret = oauth_creds.client_secret,
        code = code,
        redirect_uri = redirect_uri,
        grant_type = "authorization_code"
    }),
    headers = {
        ["Content-Type"] = "application/x-www-form-urlencoded",
        ["Accept"] = "application/json"
    }
})

if not token_res or token_res.status ~= 200 then
    ngx.log(ngx.ERR, "OAuth token exchange failed for ", provider, ": ", err or token_res.status)
    return ngx.redirect("/login.html?error=token_exchange_failed")
end

local ok, token_data = pcall(json.decode, token_res.body)
if not ok or not token_data.access_token then
    ngx.log(ngx.ERR, "Invalid token response from ", provider, ": ", token_res.body)
    return ngx.redirect("/login.html?error=invalid_token_response")
end

local access_token = token_data.access_token

-- Get user information
local user_res, err = httpc:request_uri(config.user_info_url, {
    method = "GET",
    headers = {
        ["Authorization"] = "Bearer " .. access_token,
        ["Accept"] = "application/json",
        ["User-Agent"] = "AI-Interviewer/1.0"
    }
})

if not user_res or user_res.status ~= 200 then
    ngx.log(ngx.ERR, "Failed to get user info from ", provider, ": ", err or user_res.status)
    return ngx.redirect("/login.html?error=user_info_failed")
end

local ok, user_data = pcall(json.decode, user_res.body)
if not ok then
    ngx.log(ngx.ERR, "Invalid user info response from ", provider, ": ", user_res.body)
    return ngx.redirect("/login.html?error=invalid_user_response")
end

-- Extract user information based on provider
local user_id, user_email, user_name
if provider == "google" then
    user_id = user_data.id or user_data.sub
    user_email = user_data.email
    user_name = user_data.name
elseif provider == "github" then
    user_id = tostring(user_data.id)
    user_email = user_data.email
    user_name = user_data.name or user_data.login
elseif provider == "microsoft" then
    user_id = user_data.id
    user_email = user_data.mail or user_data.userPrincipalName
    user_name = user_data.displayName
elseif provider == "apple" then
    user_id = user_data.sub
    user_email = user_data.email
    user_name = user_data.name and (user_data.name.firstName .. " " .. user_data.name.lastName) or user_data.email
end

if not user_id or not user_email then
    ngx.log(ngx.ERR, "Missing required user data from ", provider)
    return ngx.redirect("/login.html?error=incomplete_user_data")
end

-- Create session
local session_id = str.to_hex(require("resty.random").bytes(32))
local session = {
    user_id = user_id,
    user_email = user_email,
    user_name = user_name,
    provider = provider,
    access_token = access_token,
    created_at = ngx.time(),
    last_activity = ngx.time(),
    expires_at = ngx.time() + 86400  -- 24 hours
}

-- Store session in Redis
local red = redis:new()
red:set_timeout(1000)
local ok, err = red:connect("redis", 6379)
if not ok then
    ngx.log(ngx.ERR, "Failed to connect to Redis for session storage: ", err)
    return ngx.redirect("/login.html?error=session_storage_failed")
end

local success, err = red:setex("session:" .. session_id, 86400, json.encode(session))
if not success then
    ngx.log(ngx.ERR, "Failed to store session in Redis: ", err)
    red:close()
    return ngx.redirect("/login.html?error=session_storage_failed")
end

red:close()

ngx.log(ngx.INFO, "OAuth login successful for user: ", user_email, " via ", provider)

-- Set secure session cookie and redirect
local cookie_attrs = "HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=86400"
ngx.header["Set-Cookie"] = "session_id=" .. session_id .. "; " .. cookie_attrs
return ngx.redirect("/")
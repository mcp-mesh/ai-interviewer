-- oauth_initiate.lua - OAuth flow initiation
local random = require "resty.random"
local str = require "resty.string"

-- Extract provider from URI
local provider = ngx.var.uri:match("/auth/(.+)")
ngx.log(ngx.INFO, "OAuth initiation for provider: ", provider)

-- OAuth provider configurations
local oauth_configs = {
    google = {
        auth_url = "https://accounts.google.com/o/oauth2/v2/auth",
        scope = "openid email profile"
    },
    github = {
        auth_url = "https://github.com/login/oauth/authorize",
        scope = "user:email"
    },
    microsoft = {
        auth_url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        scope = "openid email profile"
    },
    apple = {
        auth_url = "https://appleid.apple.com/auth/authorize",
        scope = "email name"
    }
}

local config = oauth_configs[provider]
if not config then
    ngx.log(ngx.ERR, "Unknown OAuth provider: ", provider)
    return ngx.exit(404)
end

-- Get client ID from global config
local client_id = _G.OAUTH_CONFIG and _G.OAUTH_CONFIG[provider] and _G.OAUTH_CONFIG[provider].client_id
if not client_id then
    ngx.log(ngx.ERR, "Missing client ID for provider: ", provider)
    return ngx.redirect("/login.html?error=config_missing")
end

-- Generate state parameter for CSRF protection
local state = str.to_hex(random.bytes(16))

-- Store state in shared dict (expires in 10 minutes)
local oauth_states = ngx.shared.oauth_states
local success, err = oauth_states:set(state, provider, 600)
if not success then
    ngx.log(ngx.ERR, "Failed to store OAuth state: ", err)
    return ngx.redirect("/login.html?error=state_storage_failed")
end

-- Build authorization URL
local redirect_uri = ngx.var.scheme .. "://" .. ngx.var.host .. "/auth/callback"
local auth_url = config.auth_url .. "?" .. ngx.encode_args({
    client_id = client_id,
    redirect_uri = redirect_uri,
    scope = config.scope,
    response_type = "code",
    state = state
})

ngx.log(ngx.INFO, "Redirecting to OAuth provider: ", provider)
ngx.log(ngx.DEBUG, "OAuth URL: ", auth_url)

-- Redirect to OAuth provider
return ngx.redirect(auth_url)
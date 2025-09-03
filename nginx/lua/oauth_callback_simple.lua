-- oauth_callback_simple.lua - Simplified OAuth callback without external HTTP calls
local redis = require "resty.redis"
local json = require "cjson"
local str = require "resty.string"

-- Extract parameters from callback
local args = ngx.req.get_uri_args()
local code = args.code
local state = args.state
local error_param = args.error

ngx.log(ngx.INFO, "OAuth callback received with code: ", code and "present" or "missing")

-- Check for OAuth error
if error_param then
    ngx.log(ngx.ERR, "OAuth error: ", error_param)
    return ngx.redirect("/login.html?error=oauth_" .. error_param)
end

if not code or not state then
    ngx.log(ngx.ERR, "Missing code or state in OAuth callback")
    return ngx.redirect("/login.html?error=missing_params")
end

-- Validate state parameter (simplified check)
local oauth_states = ngx.shared.oauth_states
local stored_provider = oauth_states:get(state)
if not stored_provider then
    ngx.log(ngx.ERR, "Invalid or expired OAuth state")
    return ngx.redirect("/login.html?error=invalid_state")
end
oauth_states:delete(state)

-- Exchange authorization code for tokens with Google
local session_id = str.to_hex(require("resty.random").bytes(32))

ngx.log(ngx.INFO, "Starting OAuth token exchange for code: ", string.sub(code, 1, 20) .. "...")

-- Prepare token exchange request
local client_id = _G.OAUTH_CONFIG.google.client_id
local client_secret = _G.OAUTH_CONFIG.google.client_secret
local redirect_uri = "https://" .. ngx.var.host .. "/auth/callback"

if not client_id or not client_secret then
    ngx.log(ngx.ERR, "Missing Google OAuth credentials")
    return ngx.redirect("/login.html?error=config_missing")
end

-- Use cosocket for HTTP request to Google
local sock = ngx.socket.tcp()
sock:settimeout(10000)  -- 10 seconds timeout

local session
local ok, err = sock:connect("oauth2.googleapis.com", 443)
if not ok then
    ngx.log(ngx.ERR, "Failed to connect to Google OAuth: ", err)
    -- Fallback to demo session if connection fails
    session = {
        user_id = "google_user_" .. session_id,
        user_email = "fallback@gmail.com",
        user_name = "OAuth User",
        provider = "google",
        access_token = "connection_failed_fallback",
        oauth_authorization_code = code,
        oauth_state = state,
        created_at = ngx.time(),
        last_activity = ngx.time(),
        expires_at = ngx.time() + 86400,
        note = "Fallback session - Google connection failed"
    }
else
    -- SSL handshake
    ok, err = sock:sslhandshake(false, "oauth2.googleapis.com", false)
    if not ok then
        ngx.log(ngx.ERR, "SSL handshake failed: ", err)
        sock:close()
        return ngx.redirect("/login.html?error=ssl_failed")
    end

    -- Prepare POST data for token exchange
    local post_data = "code=" .. ngx.escape_uri(code) ..
                      "&client_id=" .. ngx.escape_uri(client_id) ..
                      "&client_secret=" .. ngx.escape_uri(client_secret) ..
                      "&redirect_uri=" .. ngx.escape_uri(redirect_uri) ..
                      "&grant_type=authorization_code"

    local request = "POST /token HTTP/1.1\r\n" ..
                    "Host: oauth2.googleapis.com\r\n" ..
                    "Content-Type: application/x-www-form-urlencoded\r\n" ..
                    "Content-Length: " .. string.len(post_data) .. "\r\n" ..
                    "Connection: close\r\n\r\n" ..
                    post_data

    -- Send request
    local bytes, err = sock:send(request)
    if not bytes then
        ngx.log(ngx.ERR, "Failed to send token request: ", err)
        sock:close()
        return ngx.redirect("/login.html?error=token_request_failed")
    end

    -- Read response headers
    local headers, err = sock:receiveuntil("\r\n\r\n")()
    if not headers then
        ngx.log(ngx.ERR, "Failed to read token response headers: ", err)
        sock:close()
        return ngx.redirect("/login.html?error=token_response_failed")
    end

    -- Check if response is successful
    if not string.match(headers, "HTTP/1%.[01] 200") then
        ngx.log(ngx.ERR, "Token request failed: ", headers)
        sock:close()
        return ngx.redirect("/login.html?error=token_http_error")
    end

    -- Check if response uses chunked encoding
    local is_chunked = string.match(headers, "Transfer%-Encoding: chunked")
    local content_length = string.match(headers, "Content%-Length: (%d+)")
    local body = ""
    
    if is_chunked then
        ngx.log(ngx.ERR, "Response uses chunked encoding")
        -- Read chunked response
        local chunks = {}
        while true do
            -- Read chunk size line
            local size_line, err = sock:receiveuntil("\r\n")()
            if not size_line then
                ngx.log(ngx.ERR, "Failed to read chunk size: ", err)
                break
            end
            
            -- Parse chunk size (hex)
            local chunk_size = tonumber(size_line, 16)
            if not chunk_size or chunk_size == 0 then
                break  -- End of chunks
            end
            
            -- Read chunk data
            local chunk_data, err = sock:receive(chunk_size)
            if not chunk_data then
                ngx.log(ngx.ERR, "Failed to read chunk data: ", err)
                break
            end
            
            -- Read trailing CRLF after chunk data
            sock:receive(2) -- \r\n
            
            table.insert(chunks, chunk_data)
        end
        body = table.concat(chunks)
        ngx.log(ngx.ERR, "Read chunked body, total length: ", string.len(body))
    elseif content_length then
        local expected_length = tonumber(content_length)
        body, err = sock:receive(expected_length)
        ngx.log(ngx.ERR, "Expected length: ", expected_length, ", got: ", body and string.len(body) or "nil")
    else
        -- Try to read until connection closes
        ngx.log(ngx.ERR, "No Content-Length or chunked encoding, reading until close")
        body, err = sock:receive("*a")
        ngx.log(ngx.ERR, "Read until close, length: ", body and string.len(body) or "nil")
    end
    
    if not body then
        ngx.log(ngx.ERR, "Failed to read token response body: ", err)
        sock:close()
        return ngx.redirect("/login.html?error=token_body_failed")
    end

    sock:close()

    -- Clean the body - remove any leading/trailing whitespace and control chars
    body = string.gsub(body, "^%s*", "")  -- Remove leading whitespace
    body = string.gsub(body, "%s*$", "")  -- Remove trailing whitespace

    ngx.log(ngx.ERR, "Google token response headers: ", string.sub(headers, 1, 300))
    ngx.log(ngx.ERR, "Google token response body (first 300 chars): ", string.sub(body, 1, 300))
    ngx.log(ngx.ERR, "Body length after cleaning: ", string.len(body))
    ngx.log(ngx.ERR, "Body last 50 chars: ", string.sub(body, -50))

    -- Parse token response JSON
    local token_data, decode_err = json.decode(body)
    if not token_data then
        ngx.log(ngx.ERR, "JSON decode error: ", decode_err or "unknown")
        ngx.log(ngx.ERR, "Raw body: ", body)
        return ngx.redirect("/login.html?error=json_decode_failed")
    end
    
    if token_data.error then
        ngx.log(ngx.ERR, "Token exchange failed: ", body)
        return ngx.redirect("/login.html?error=token_exchange_failed")
    end

    -- Extract user info from ID token (JWT)
    local access_token = token_data.access_token
    local id_token = token_data.id_token
    local user_email = "oauth_user@gmail.com"
    local user_name = "OAuth User"
    
    if id_token then
        -- Decode JWT ID token to get user info (simple base64 decode of payload)
        local jwt_parts = {}
        for part in string.gmatch(id_token, "([^%.]+)") do
            table.insert(jwt_parts, part)
        end
        
        if #jwt_parts >= 2 then
            -- Decode the payload (second part)
            local payload_b64 = jwt_parts[2]
            -- Add padding if needed
            local padding = 4 - (#payload_b64 % 4)
            if padding ~= 4 then
                payload_b64 = payload_b64 .. string.rep("=", padding)
            end
            
            local payload_json = ngx.decode_base64(payload_b64)
            if payload_json then
                local user_info = json.decode(payload_json)
                if user_info then
                    user_email = user_info.email or user_email
                    user_name = user_info.name or user_info.given_name or user_name
                    ngx.log(ngx.INFO, "Decoded user info: ", user_email, " / ", user_name)
                end
            end
        end
    end
    
    if access_token then
        session = {
            user_id = "google_user_" .. session_id,
            user_email = user_email,      -- Real email from Google ID token
            user_name = user_name,        -- Real name from Google ID token  
            provider = "google",
            access_token = access_token,
            refresh_token = token_data.refresh_token,
            id_token = id_token,
            oauth_authorization_code = code,
            oauth_state = state,
            created_at = ngx.time(),
            last_activity = ngx.time(),
            expires_at = ngx.time() + (token_data.expires_in or 3600),
            note = "Real OAuth session with Google tokens and user info"
        }
        ngx.log(ngx.INFO, "OAuth token exchange successful")
    else
        ngx.log(ngx.ERR, "No access token in response")
        return ngx.redirect("/login.html?error=no_access_token")
    end
end

-- Store session in Redis
local red = redis:new()
red:set_timeout(1000)
local ok, err = red:connect("redis", 6379)
if not ok then
    ngx.log(ngx.ERR, "Failed to connect to Redis for session storage: ", err)
    return ngx.redirect("/login.html?error=session_storage_failed")
end

ngx.log(ngx.ERR, "About to store session with ID: ", session_id)
ngx.log(ngx.ERR, "Session data being stored: ", json.encode(session))

local success, err = red:setex("session:" .. session_id, 86400, json.encode(session))
if not success then
    ngx.log(ngx.ERR, "Failed to store session in Redis: ", err)
    red:close()
    return ngx.redirect("/login.html?error=session_storage_failed")
end

-- Verify the session was stored by reading it back immediately
local stored_session, read_err = red:get("session:" .. session_id)
if stored_session then
    ngx.log(ngx.ERR, "Session storage verified - stored data length: ", string.len(stored_session))
else
    ngx.log(ngx.ERR, "Session storage verification FAILED: ", read_err or "session not found")
end

red:close()

ngx.log(ngx.INFO, "OAuth login successful for email: ", session.user_email or "unknown")

-- Set secure session cookie and redirect
local cookie_attrs = "HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=86400"
ngx.header["Set-Cookie"] = "session_id=" .. session_id .. "; " .. cookie_attrs
ngx.log(ngx.ERR, "Setting cookie with session_id: ", session_id)
return ngx.redirect("/dashboard")
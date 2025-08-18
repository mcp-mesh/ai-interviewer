-- auth_check.lua - Session validation and user context extraction
local redis = require "resty.redis"
local json = require "cjson"

-- DEV_MODE bypass for development  
local dev_mode = ngx.var.dev_mode
ngx.log(ngx.INFO, "DEV_MODE check: ", dev_mode or "nil")
if dev_mode == "true" then
    ngx.log(ngx.INFO, "DEV_MODE: Bypassing authentication")
    -- Set fake bearer token for development
    ngx.var.bearer_token = "dev_fake_bearer_token"
    return  -- Skip authentication in dev mode
end

-- Get session cookie
local session_cookie = ngx.var.cookie_session_id
ngx.log(ngx.ERR, "Auth check - session cookie received: ", session_cookie or "nil")
if not session_cookie then
    ngx.log(ngx.INFO, "No session cookie found, redirecting to login")
    return ngx.redirect("/login.html")
end

-- Connect to Redis
local red = redis:new()
red:set_timeout(1000) -- 1 second
local ok, err = red:connect("ai-interviewer-redis.ai-interviewer.svc.cluster.local", 6379)
if not ok then
    ngx.log(ngx.ERR, "Failed to connect to Redis: ", err)
    return ngx.redirect("/login.html?error=redis_connection")
end

-- Validate session
ngx.log(ngx.ERR, "Auth check - looking for session key: ", "session:" .. session_cookie)
local session_data, err = red:get("session:" .. session_cookie)
ngx.log(ngx.ERR, "Auth check - Redis get result: ", session_data or "nil", ", error: ", err or "none")
if not session_data or session_data == ngx.null then
    ngx.log(ngx.INFO, "Invalid or expired session: ", session_cookie)
    red:close()
    return ngx.redirect("/login.html?error=invalid_session")
end

-- Parse session data
local ok, session = pcall(json.decode, session_data)
if not ok or type(session) ~= "table" then
    ngx.log(ngx.ERR, "Failed to parse session data - ok: ", ok, ", session type: ", type(session))
    ngx.log(ngx.ERR, "Session data: ", string.sub(session_data, 1, 200))
    red:del("session:" .. session_cookie)
    red:close()
    return ngx.redirect("/login.html?error=invalid_session_data")
end

local current_time = ngx.time()

-- Check if session is expired
if session.expires_at and session.expires_at < current_time then
    ngx.log(ngx.INFO, "Session expired for user: ", session.user_email or "unknown")
    red:del("session:" .. session_cookie)
    red:close()
    return ngx.redirect("/login.html?error=session_expired")
end

-- Set bearer token variable for Authorization header 
-- For Google, use the existing id_token JWT
-- For GitHub/others, create a simple JWT with user info from session
if session.id_token then
    -- Google: use the real JWT id_token from Google OAuth
    ngx.var.bearer_token = session.id_token
else
    -- GitHub/others: create a simple JWT with user info from session
    -- This keeps the backend stateless - no Redis lookups needed
    local user_jwt_payload = {
        email = session.user_email,
        name = session.user_name,
        provider = session.provider,
        sub = session.user_id,
        iat = session.created_at,
        exp = session.expires_at
    }
    
    -- Create a simple base64-encoded JWT (header.payload.signature)
    local jwt_header = '{"alg":"none","typ":"JWT"}'
    local jwt_payload = json.encode(user_jwt_payload)
    
    -- Base64 encode header and payload
    local encoded_header = ngx.encode_base64(jwt_header):gsub("=", "")
    local encoded_payload = ngx.encode_base64(jwt_payload):gsub("=", "")
    
    -- Create unsigned JWT (we trust nginx, so no signature needed)
    local user_jwt = encoded_header .. "." .. encoded_payload .. "."
    ngx.var.bearer_token = user_jwt
end

-- Update session last activity
session.last_activity = current_time
red:setex("session:" .. session_cookie, 86400, json.encode(session)) -- Extend for 24 hours

red:close()

ngx.log(ngx.INFO, "Authentication successful for user: ", session.user_email or "unknown")
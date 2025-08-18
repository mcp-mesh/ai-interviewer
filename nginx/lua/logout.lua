-- logout.lua - Session cleanup and logout
local redis = require "resty.redis"

ngx.log(ngx.INFO, "User logout requested")

local session_cookie = ngx.var.cookie_session_id
if session_cookie then
    -- Connect to Redis and delete session
    local red = redis:new()
    red:set_timeout(1000)
    local ok, err = red:connect("redis", 6379)
    if ok then
        local result, err = red:del("session:" .. session_cookie)
        if result then
            ngx.log(ngx.INFO, "Session deleted successfully: ", session_cookie)
        else
            ngx.log(ngx.ERR, "Failed to delete session: ", err)
        end
        red:close()
    else
        ngx.log(ngx.ERR, "Failed to connect to Redis for logout: ", err)
    end
end

-- Clear session cookie and redirect to login
local cookie_attrs = "HttpOnly; Secure; SameSite=Lax; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT"
ngx.header["Set-Cookie"] = "session_id=; " .. cookie_attrs

ngx.log(ngx.INFO, "Logout completed, redirecting to homepage")
return ngx.redirect("/?message=logged_out")
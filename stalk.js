var http = require('http')
  , redis = require('redis')
  , sys = require('sys')
  , querystring = require('querystring')

var REDIS_HOST = 'localhost'
  , REDIS_PORT = 6379
  , REDIS_DB = 0

var client = redis.createClient(REDIS_PORT, REDIS_HOST)

client.on('error', function (err) {
  sys.puts('Redis error ' + err)
})

var buffer = new Buffer('{}')

function update() {
  sys.puts('[' + new Date() + '] Updating stalk data')
  // Python stores activity scores as seconds since epoch
  var since = (new Date().valueOf() - (30 * 60 * 1000)) / 1000
  var users = []
  // Get recently active users and when they were last seen
  client.zrangebyscore('au', since, '+inf', 'withscores', function(err, active) {
    var getKeys = []
    // Iterate back to front to get most recent users first
    for (var i = active.length - 2; i >= 0; i -= 2) {
      var id = active[i]
      users.push({id: id, seen: active[i + 1]})
      getKeys.push('u:' + id + ':un')
      getKeys.push('u:' + id + ':d')
    }

    if (!users.length) {
      buffer = new Buffer(JSON.stringify(users))
      setTimeout(update, 5000)
      return
    }

    sys.puts(users.length + ' active')

    // Get usernames and what they were last seen doing
    client.mget(getKeys, function(err, details) {
      var userIndex = 0
      for (var i = 0, l = details.length; i < l; i += 2) {
        var user = users[userIndex++]
        user.username = details[i]
        user.doing = details[i + 1]
      }
      buffer = new Buffer(JSON.stringify(users))
      setTimeout(update, 5000)
    })
  })
}

var server = http.createServer(function (req, res) {
  var callback = require('url').parse(req.url, true).query['callback'] || 'callback'
  res.write(callback + '(')
  res.write(buffer)
  res.end(')')
})

server.listen(8001, '127.0.0.1')
sys.puts('Stalking users at http://127.0.0.1:8001/')

update()

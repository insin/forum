var dom = DOMBuilder.dom

function update() {
  $.getJSON('http://localhost:8001/?callback=?', function(data) {
    $body = $('#stalkUsers')
    $body.empty()
    $.each(data, function(i, user) {
      $body.append(
        dom.TR({'class': (i % 2 == 0 ? 'odd' : 'even')}
        , dom.TD(dom.A({href: '/user/' + user.id}, user.username))
        , dom.TD(new Date(user.seen * 1000).toString().substring(0, 24))
        , dom.TD({innerHTML: user.doing})
        )
      )
    })
    setTimeout(update, 5000)
  })
}

$(function() {
  update()
})
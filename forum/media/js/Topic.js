// Create Fast Reply controls
if (createFastReplyControls)
$(function() {
  if ($('#topic-actions-bottom').size() > 0) {
    $('#topic-actions-bottom')
      .prepend(document.createTextNode(' | '))
      .prepend(
        $('<a href="#fast-reply">Fast Reply</a>').click(function() {
          $("#fast-reply").toggle()
        })
      )
  }

  if ($("#fast-reply-buttons").size() > 0) {
    $("#fast-reply-buttons").append(
      $('<input type="button" value="Close Fast Reply">').click(function() {
        $("#fast-reply").toggle()
      })
    )
  }
})

$(function() {
  if ($('#emoticons img').size() > 0) {
    $('#emoticons img').addClass('clickable').click(function() {
      document.forms[0].elements['body'].value += this.alt + ' '
    })
  }
})

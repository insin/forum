var Paginator = {
  jumpToPage: function(pages) {
    var page = prompt('Enter a number between 1 and ' + pages + ' to jump to that page', '')
    if (page != undefined) {
      page = parseInt(page, 10)
      if (!isNaN(page) && page > 0 && page <= pages) {
        window.location.href = '?page=' + page
      }
    }
  }
}

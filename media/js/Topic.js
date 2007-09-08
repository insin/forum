// Create Fast Reply controls
jQuery(function()
{
    if (jQuery("#topic-actions-bottom").size() > 0)
    {
        jQuery("#topic-actions-bottom")
        .prepend(document.createTextNode(" | "))
        .prepend(jQuery('<a href="#fast-reply">Fast Reply</a>').click(function()
        {
            jQuery("#fast-reply").toggle();
        }));
    }

    if (jQuery("#fast-reply-buttons").size() > 0)
    {
        jQuery("#fast-reply-buttons")
        .append(jQuery('<input type="button" value="Close Fast Reply">').click(function()
        {
            jQuery("#fast-reply").toggle();
        }));
    }
});
// Create Fast Reply controls
jQuery(function()
{
    if (jQuery("#topic-actions-bottom").size() > 0)
    {
        jQuery('<a href="#fast-reply">Fast Reply</a>').click(function()
        {
            jQuery("#fast-reply").toggle();
        }).prependTo("#topic-actions-bottom");
    }

    if (jQuery("#fast-reply-buttons").size() > 0)
    {
        jQuery('<input type="button" value="Close Fast Reply">').click(function()
        {
            jQuery("#fast-reply").toggle();
        }).appendTo("#fast-reply-buttons");
    }
});
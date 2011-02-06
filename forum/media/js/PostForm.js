jQuery(function()
{
    if (jQuery("#emoticons img").size() > 0)
    {
        jQuery("#emoticons img").addClass("clickable").click(function()
        {
            document.forms[0].elements["body"].value += this.alt + " ";
        });
    }
});
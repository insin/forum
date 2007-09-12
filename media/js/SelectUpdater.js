if (typeof(Object.extend) == "undefined")
{
    /**
     * Used by SelectUpdater.
     *
     * Extends the properties of the destination object with those of the source
     * object.
     *
     * @param {Object} destination the Object whose properties are to be
     *                             extended.
     * @param {Object} source the Object whose properties are to used for
     *                        extension.
     * @addon
     */
    Object.extend = function(destination, source)
    {
        for (property in source)
        {
            destination[property] = source[property];
        }
        return destination;
    };
}

if (typeof(Function.prototype.bind) == "undefined")
{
    /**
     * Used by SelectUpdater.
     *
     * Binds this Function with a "calling object" - the object which "this"
     * points to when the Function is executed.
     *
     * @param {Object} context the object to be used as <code>this</code> when
     *                         this Function is executed.
     *
     * @return a Function binding this function with <code>context</code> as its
     *         calling object.
     * @type Function
     * @addon
     */
    Function.prototype.bind = function(context)
    {
        var __method = this;
        return function()
        {
            __method.apply(context, arguments);
        }
    };
}

/**
 * Encapsulates a relationship between a "parent" and a "child" select element,
 * where changing the selected value in the parent select should result in the
 * options available in the child select being updated according to the value
 * which was selected, as defined by a provided mapping Object.
 *
 * @param {String} parentSelectId the id of the "parent" select element
 * @param {String} childSelectId the id of the "child" select element
 * @param {Object} childOptionMap an object mapping selected values in the
 *                                parent select to a list of objects containing
 *                                option details for the child select, each of
 *                                which has a "text" and "value" property.
 * @param {Object} options an object which may specify the following
 *                         options:
 * <dl>
 * <dt><code>updateOnCreate</code></dt>
 * <dd>if <code>true</code>, if both select DOM Elements are available and the
 * parent has an option selected, the child select will be updated immediately
 * upon creation of this SelectUpdater.</dd>
 * </dl>
 *
 * @constructor
 */
function SelectUpdater(parentSelectId, childSelectId, childOptionMap, options)
{
    /**
     * The <code>id</code> of the Select which acts as the "parent".
     */
    this.parentSelectId = parentSelectId;
    /**
     * The <code>id</code> of the Select which acts as the "child".
     */
    this.childSelectId = childSelectId;
   /**
    * An object mapping selected values in the parent select to a list of objects
    * containing option details for the child select, each of which should have a
    * "text" and "value" property.
    */
    this.childOptionMap = childOptionMap;
    /**
     * A list of SelectUpdaters which manage Selects whose contents depend on
     * the contents of any of the Selects managed by this SelectUpdater.
     */
    this.dependents = [];
    /**
     * Additional options for this SelectUpdater.
     */
    this.options = Object.extend({
        updateOnCreate: false
    }, options);

    if (this.options.updateOnCreate == true)
    {
        // If both select DOM Elements are available and the parent has an option
        // selected, update the child select immediately.
        var parentSelect = document.getElementById(parentSelectId);
        if (parentSelect !== null && parentSelect.selectedIndex > 0 &&
            document.getElementById(childSelectId) !== null)
        {
            this.update();
        }
    }

    // Attach an event handling function to the parent select
    document.getElementById(parentSelectId).onchange = this.update.bind(this);
};

/**
 * Updates the state of the child select according to the current state of the
 * parent select.
 */
SelectUpdater.prototype.update = function()
{
    // Get the child select element
    var childSelect = document.getElementById(this.childSelectId);

    // Empty the child select
    while (childSelect.options.length > 0)
    {
        childSelect.remove(0);
    }

    // Populate the child select with a "blank" option
    childSelect.options.add(new Option("---------", ""));

    // Determine if an item was selected in the parent select
    var parentSelect = document.getElementById(this.parentSelectId);
    if (parentSelect.selectedIndex > 0)
    {
        // Find the options which should be displayed in the child select
        var selectedValue = parentSelect.options[parentSelect.selectedIndex].value;
        var childOptions = this.childOptionMap[selectedValue];
        if (typeof(childOptions) != "undefined")
        {
            // Populate the child select with the specified options
            for (var i = 0; i < childOptions.length; i++)
            {
                var childOption = childOptions[i];
                childSelect.options.add(new Option(childOption.text, childOption.value));
            }
        }
    }

    // Update any dependent SelectUpdaters
    for (var i = 0; i < this.dependents.length; i++)
    {
        this.dependents[i].update();
    }
};

/**
 * Adds a dependent SelectUpdater.
 *
 * @param {SelectUpdater} selectUpdater a SelectUpdater whose managed selects
 *                                      depend on the contents of the selects
 *                                      managed by this SelectUpdater.
 */
SelectUpdater.prototype.addDependent = function(selectUpdater)
{
    this.dependents.push(selectUpdater);
};
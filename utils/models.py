from django.db import connection, transaction

def update(model_instance, *args):
    """
    Updates only specified fields of the given model instance.
    """
    opts = model_instance._meta
    fields = [opts.get_field(f) for f in args]
    db_values = [f.get_db_prep_save(f.pre_save(model_instance, False)) for f in fields]
    if db_values:
        connection.cursor().execute("UPDATE %s SET %s WHERE %s=%%s" % \
            (connection.ops.quote_name(opts.db_table),
             ','.join(['%s=%%s' % connection.ops.quote_name(f.column) for f in fields]),
             connection.ops.quote_name(opts.pk.column)),
             db_values + opts.pk.get_db_prep_lookup('exact', model_instance.pk))
        transaction.commit_unless_managed()

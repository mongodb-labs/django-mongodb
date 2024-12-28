def setup(app):
    app.add_crossref_type(
        directivename="fieldlookup",
        rolename="lookup",
        indextemplate="pair: %s; field lookup type",
    )

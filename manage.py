#! /usr/bin/env python
from flask.ext.script import Manager
from naverwebtoonfeeds import app

manager = Manager(app)

@manager.command
def resetdb():
    """Delete all tables (if any) in the database and recreate them."""
    from naverwebtoonfeeds import db
    try:
        db.drop_all()
    except:
        pass
    db.create_all()

@manager.command
def update(debug=False):
    """Update local data to date with Naver Comics."""
    if debug:
        app.config['DEBUG'] = True
    from naverwebtoonfeeds import update_series_info
    update_series_info(force_update=True, should_update_chapters=True)

@manager.command
def test():
    """Test the application with doctest."""
    import doctest, naverwebtoonfeeds
    doctest.testmod(naverwebtoonfeeds)

if __name__ == '__main__':
    manager.run()

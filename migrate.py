from config import config

from library import app
from database import Database
from models import Meta

from migration import *
import migration

class DatabaseMigration(object):
    def __init__(self):
        self.db = Database(app)

    def get_database_version(self):
        """
        DatabaseMigration.get_database_version(): returns the int value of db version
        Params:
        - None
        Returns:
        - (int) : the version of the database
        """
        version = Meta.query.filter_by(key="DB_VERSION").first()
        return int(version.value)

    def update_database_version(self, version=None):
        """
        DatabaseMigration.update_database_version() - updates a db version
        Params:
        - version (int) [optional] : the version to set.  if ommitted, increments version
        Returns:
        - None
        """
        current_version = Meta.query.filter_by(key="DB_VERSION").first()
        if version == None:
            new_version = str(int(current_version.value) + 1)
        else:
            new_version = str(version)
        current_version.value = new_version
        self.db.session.add(current_version)
        self.db.session.commit()

    def update_database(self):
        current_version = self.get_database_version()
        print "current db version is " + str(current_version)
        migration_contents = sorted(dir(migration))
        for contents in migration_contents:
            parts = contents.split("_")
            if parts[0]: #does not start with _
                script_version = int(parts[0])
                if script_version > int(current_version):
                    print "running  " + contents
                    module = getattr(migration, contents)
                    module.main()
                    self.update_database_version()
                    
        current_version = self.get_database_version()
        print "current db version is " + str(current_version)
        
if __name__=="__main__":
    dm = DatabaseMigration()
    dm.update_database()

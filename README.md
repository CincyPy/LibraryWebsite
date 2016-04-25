# BookUs
This is the repository for the BookUs project

A group of CincyPy members created the BookUs website for [Kenton County Public Library](http://www.kentonlibrary.org/) modeled after ["My Librarian"](https://multcolib.org/my-librarian) project at the Multnomah County Library using Python and [Flask](http://flask.pocoo.org/). Our [beta site] (http://library.cincypy.com/) is set to launch shortly. The purpose of the app is to help connect people to library staff who may share their interests and reading taste. By making profiles of each librarian, users can browse and connect to get personalized recommendations. We hope to develop features based on what users request. CincyPy members contributed their time and all the code as a way to help the community, make friends and develop skills in web development. If you'd like to do the same, attend the next [CincyPy Meetup] (http://www.meetup.com/CincyPy/). Code is available for reuse at your library or organization thanks to the generosity of CincPy and under a [GNU license] (http://www.gnu.org/licenses/gpl-3.0.en.html).

# Setup
* Clone the repository, `git clone https://github.com/CincyPy/LibraryWebsite.git`
* Create a virtualenv, using `virtualenv -p python env`
* Activate the virtualenv, on windows, `env\Scripts\activate.bat`, on UNIX, `source env/bin/activate`
* Install dependencies. `pip install -r requirements.txt`
* Set the environment variable to test. UNIX: `export LIBRARY_ENV=test` Windows: `set LIBRARY_ENV test`.
* Run the tests. `python tests.py -vf`.
* Set the environment variable to production. UNIX: `export LIBRARY_ENV=production` Windows: `set LIBRARY_ENV production`.
* Create the database. `python models.py`.  If it gives you an error, you may already have an existing db.
* Run the server. `python library.py`

### Initialize Database
```
$ python models.py
```

### Quick interactive shell with app context
```
python -i shell.py
>>> Staff.query.get()
<models.Staff object at 0x7f955fbd11d0>
>>> _.emailaddress
u'KentonCountyLibrary@gmail.com'
```

# Authors
* Ann
* Cindy
* John
* Carl
* Leila
* Michael
* Joe
* Brian

If you'd like to contribute, join [CincyPy](http://www.meetup.com/CincyPy/) and send us a message or come to our next [meeting](http://www.meetup.com/CincyPy/).

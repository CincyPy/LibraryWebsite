# LibraryWebsite
This is the repository for the Library Website project

A group of CincyPy members is creating a website for [Kenton County Public Library](http://www.kentonlibrary.org/) modeled after ["My Librarian"](https://multcolib.org/my-librarian) project at the Multnomah County Library. We are using Python and [Flask](http://flask.pocoo.org/).

#Setup
* Clone the repository, `git clone https://github.com/CincyPy/LibraryWebsite.git`
* Create a virtualenv, using `virtualenv -p python env`
* Activate the virtualenv, on windows, `env\Scripts\activate.bat`, on UNIX, `source env/bin/activate`
* Install dependencies. `pip install -r requirements.txt`
* Create the database. `python db.py library.db`.  If it gives you an error, you may already have an existing db.
* Run the server. `python library.py`

### Initialize Database
```
$ python models.py
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

If you'd like to contribute, join [CincyPy] (http://www.meetup.com/CincyPy/) and send us a message or come to our next [meeting](http://www.meetup.com/CincyPy/).

--new text for the new branch

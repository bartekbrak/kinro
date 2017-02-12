# Kinro - simple time tracking for the paranoid

Goals:

* Visualize one's workday patterns.
* Calculate focus factor - time spent working focused vs idle work time (disabled for the moment)
* Calculate other metrics, averages

More broadly:

* Reduce stress connected to one's work pace, break habits, ability to 
focus
* Collect data to be able to notice long term patterns
* Should make remote work easier

# Screenshot

![alt tag](https://raw.githubusercontent.com/bartekbrak/kinro/master/screen.png)

Also see the demo data to get the hang of it.

# Datamodel

The goal is to keep it simple, close to real life. 

* TimeSpan - activity with start and end
* Bucket - TimeSpans fall into buckets, buckets are for measuring time 
spent on something

See the docstrings for longer musings

# Front-end

I don't care about the looks, the UI is minimal and works for me, I 
hope someone can add another one, the views should give enough data but 
we can add more. Nothing stops us from developing alternative UIs and 
add them under different urls, I mainly use bash+curl to operate the 
timers.

# Standards

* python 3.5
* YYYY-MM-DD as date format
* 100 chars per line
* Keep tests to minimum, on purpose, keep icode so simple that tests are not necessary,
* The default dashboard uses modern Javascript (is that ECMA6?) so it 
  won't work on Netscape Navigator 2.3 and your grandma's funny browser. 

# Install 

```
# pseudo instructions, no hand holding
git clone
virtualenv
source activate
pip install -r requirements.txt
# optional, suit yourself
cp local_settings.py.template local_settings.py
# you might want to see the demo database
cp demo.sqlite3 db.sqlite3
# optional 
./manage.py createsuperuser
./manage.py migrate
./manage.py runserver
```

# Run tests
```
pip install -r requirements_dev.txt
# Figure out how to install core module yourself, I don't care.
py.test
# there is one test, so far
```

# TODO

* Make project timezone aware.
* Provide user auth... but what for?
* Add exporters to other apps, harvest et cetera...
* Revise docstrings
* Fix FIXMEs
* some code was rushed, especially in models, not the data model itself 
  though
* Let the default dashboard take dates in URL
* Let the start/stop buttons work in some other way than opening a new 
windows, gods!

# History and Changelog

* 2017-02-12 Clean up, add daily target module, many UI improvements, I consider this to be good
  enough to release to public
* 2016-09-27 Version 1: alpha, I've been using tha app for two months, 
testing ideas and arriving at some stable minimal base
* 2016-07-22 no version, enough code to start logging
* 2016 May, I get slighty pissed when Lars says that we could work 5 
times as much but I have nothing to prove how much we actually work, so 
I start designing in my mind

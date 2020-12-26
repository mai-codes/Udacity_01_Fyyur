#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort, jsonify
from flask_moment import Moment
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import re
from datetime import datetime
from operator import itemgetter
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
#initialize migration
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Genre(db.Model):
    __tablename__ = 'Genre'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

# Association tables for Artist to Genre and Venue to Genre
artist_genre_table = db.Table('artist_genre_table',
  db.Column('genre_id', db.Integer, db.ForeignKey('Genre.id'), primary_key=True),
  db.Column('artist_id', db.Integer, db.ForeignKey('Artist.id'), primary_key=True)
)
venue_genre_table = db.Table('venue_genre_table',
  db.Column('genre_id', db.Integer, db.ForeignKey('Genre.id'), primary_key=True),
  db.Column('venue_id', db.Integer, db.ForeignKey('Venue.id'), primary_key=True)
)


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    # link the associative table for the m2m relationship with genre
    genres = db.relationship('Genre', secondary=venue_genre_table, backref=db.backref('venues'))
    # add missing information
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(120))
    # Venue is the parent a Show
    # In the parent is where we put the db.relationship in SQLAlchemy
    shows = db.relationship('Show', backref='venue', lazy=True) 

    def __repr__(self):
      return f'<Venue {self.id} {self.name}>'


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    # link the associative table for the m2m relationship with genre
    genres = db.relationship('Genre', secondary=artist_genre_table, backref=db.backref('artists'))
    # add missing info
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship('Show', backref='artist', lazy=True)

    def __repr__(self):
      return f'<Artist {self.id} {self.name}>'


class Show(db.Model):
    __tablename__ = 'Show'
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)    # Start time required field
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)  
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)

    def __repr__(self):
      return f'<Show {self.id} {self.start_time} artist_id={artist_id} venue_id={venue_id}>'

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
    format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
    format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # COMPLETE: replace with real venues data.
  # Get data on the venues and populate the data list (grouped per city)
  venues = Venue.query.all() 
  # Initialize dictionary where city, state, and venues are keys
  data = []   
  cities_states = set()

  for venue in venues:
    cities_states.add((venue.city, venue.state)) 
  cities_states = list(cities_states)
  cities_states.sort(key=itemgetter(1,0))
  now = datetime.now()    

  # Now iterate over the unique values to seed the data dictionary with city/state locations
  for loc in cities_states:
    venues_list = []
    for venue in venues:
      if (venue.city == loc[0]) and (venue.state == loc[1]):
        venue_shows = Show.query.filter_by(venue_id=venue.id).all()
        num_upcoming = 0
        for show in venue_shows:
          if show.start_time > now:
            num_upcoming += 1
          venues_list.append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": num_upcoming
          })
    data.append({
      "city": loc[0],
      "state": loc[1],
      "venues": venues_list
    })
  return render_template('pages/venues.html', areas=data)

  # Original info:
  # data=[{
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "venues": [{
  #     "id": 1,
  #     "name": "The Musical Hop",
  #     "num_upcoming_shows": 0,
  #   }, {
  #     "id": 3,
  #     "name": "Park Square Live Music & Coffee",
  #     "num_upcoming_shows": 1,
  #   }]
  # }, {
  #   "city": "New York",
  #   "state": "NY",
  #   "venues": [{
  #     "id": 2,
  #     "name": "The Dueling Pianos Bar",
  #     "num_upcoming_shows": 0,
  #   }]
  # }]

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # COMPLETE: implement search on artists with partial string search. Ensure it is case-insensitive.
  search_term = request.form.get('search_term', '').strip()
  # Use filter when doing LIKE search (i=insensitive to case)
  venues = Venue.query.filter(Venue.name.ilike('%' + search_term + '%')).all()   
  venue_list = []
  now = datetime.now()
  for venue in venues:
    venue_shows = Show.query.filter_by(venue_id=venue.id).all()
    num_upcoming = 0
    for show in venue_shows:
      if show.start_time > now:
        num_upcoming += 1

      venue_list.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": num_upcoming 
      })

  response = {
    "count": len(venues),
    "data": venue_list
  }
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

  # response={
  #   "count": 1,
  #   "data": [{
  #     "id": 2,
  #     "name": "The Dueling Pianos Bar",
  #     "num_upcoming_shows": 0,
  #   }]
  # }

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # COMPLETE: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.get(venue_id)   # Returns object by primary key, or None
  print(venue)
  if not venue:
    # Didn't return one, user must've hand-typed a link into the browser that doesn't exist
    # Redirect home
    return redirect(url_for('index'))
  else:
    # genres needs to be a list of genre strings for the template
    genres = [ genre.name for genre in venue.genres ]
      
    # Get a list of shows, and count the ones in the past and future
    past_shows = []
    past_shows_count = 0
    upcoming_shows = []
    upcoming_shows_count = 0
    now = datetime.now()
    for show in venue.shows:
      if show.start_time > now:
        upcoming_shows_count += 1
        upcoming_shows.append({
          "artist_id": show.artist_id,
          "artist_name": show.artist.name,
          "artist_image_link": show.artist.image_link,
          "start_time": format_datetime(str(show.start_time))
        })
        if show.start_time < now:
          past_shows_count += 1
          past_shows.append({
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": format_datetime(str(show.start_time))
          })

      data = {
        "id": venue_id,
        "name": venue.name,
        "genres": genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": (venue.phone[:3] + '-' + venue.phone[3:6] + '-' + venue.phone[6:]),
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "past_shows_count": past_shows_count,
        "upcoming_shows": upcoming_shows,
        "upcoming_shows_count": upcoming_shows_count
      }
  return render_template('pages/show_venue.html', venue=data)

  # data1={
  #   "id": 1,
  #   "name": "The Musical Hop",
  #   "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
  #   "address": "1015 Folsom Street",
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "phone": "123-123-1234",
  #   "website": "https://www.themusicalhop.com",
  #   "facebook_link": "https://www.facebook.com/TheMusicalHop",
  #   "seeking_talent": True,
  #   "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
  #   "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
  #   "past_shows": [{
  #     "artist_id": 4,
  #     "artist_name": "Guns N Petals",
  #     "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
  #     "start_time": "2019-05-21T21:30:00.000Z"
  #   }],
  #   "upcoming_shows": [],
  #   "past_shows_count": 1,
  #   "upcoming_shows_count": 0,
  # }
  # data2={
  #   "id": 2,
  #   "name": "The Dueling Pianos Bar",
  #   "genres": ["Classical", "R&B", "Hip-Hop"],
  #   "address": "335 Delancey Street",
  #   "city": "New York",
  #   "state": "NY",
  #   "phone": "914-003-1132",
  #   "website": "https://www.theduelingpianos.com",
  #   "facebook_link": "https://www.facebook.com/theduelingpianos",
  #   "seeking_talent": False,
  #   "image_link": "https://images.unsplash.com/photo-1497032205916-ac775f0649ae?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=750&q=80",
  #   "past_shows": [],
  #   "upcoming_shows": [],
  #   "past_shows_count": 0,
  #   "upcoming_shows_count": 0,
  # }
  # data3={
  #   "id": 3,
  #   "name": "Park Square Live Music & Coffee",
  #   "genres": ["Rock n Roll", "Jazz", "Classical", "Folk"],
  #   "address": "34 Whiskey Moore Ave",
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "phone": "415-000-1234",
  #   "website": "https://www.parksquarelivemusicandcoffee.com",
  #   "facebook_link": "https://www.facebook.com/ParkSquareLiveMusicAndCoffee",
  #   "seeking_talent": False,
  #   "image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
  #   "past_shows": [{
  #     "artist_id": 5,
  #     "artist_name": "Matt Quevedo",
  #     "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
  #     "start_time": "2019-06-15T23:00:00.000Z"
  #   }],
  #   "upcoming_shows": [{
  #     "artist_id": 6,
  #     "artist_name": "The Wild Sax Band",
  #     "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #     "start_time": "2035-04-01T20:00:00.000Z"
  #   }, {
  #     "artist_id": 6,
  #     "artist_name": "The Wild Sax Band",
  #     "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #     "start_time": "2035-04-08T20:00:00.000Z"
  #   }, {
  #     "artist_id": 6,
  #     "artist_name": "The Wild Sax Band",
  #     "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #     "start_time": "2035-04-15T20:00:00.000Z"
  #   }],
  #   "past_shows_count": 1,
  #   "upcoming_shows_count": 1,
  # }
  # data = list(filter(lambda d: d['id'] == venue_id, [data1, data2, data3]))[0]

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # COMPLETE: insert form data as a new Venue record in the db, instead
  form = VenueForm()
  name = form.name.data.strip()
  city = form.city.data.strip()
  state = form.state.data
  address = form.address.data.strip()
  phone = form.phone.data
  # strip anything from phone that isn't a number
  phone = re.sub('\D', '', phone) # e.g. (819) 392-1234 --> 8193921234
  genres = form.genres.data  # ['Alternative', 'Classical', 'Country']
  seeking_talent = True if form.seeking_talent.data == 'Yes' else False
  seeking_description = form.seeking_description.data.strip()
  image_link = form.image_link.data.strip()
  website = form.website.data.strip()
  facebook_link = form.facebook_link.data.strip()
  
  # Redirect back to form if errors in form validation
  if not form.validate():
      flash( form.errors )
      return redirect(url_for('create_venue_submission'))

  else:
      error_in_insert = False
      try:
          new_venue = Venue(name=name, city=city, state=state, address=address, phone=phone, \
              seeking_talent=seeking_talent, seeking_description=seeking_description, image_link=image_link, \
              website=website, facebook_link=facebook_link)
          for genre in genres:
              fetch_genre = Genre.query.filter_by(name=genre).one_or_none() 
              if fetch_genre:
                  new_venue.genres.append(fetch_genre)
              else:
                  new_genre = Genre(name=genre)
                  db.session.add(new_genre)
                  new_venue.genres.append(new_genre) 
          db.session.add(new_venue)
          db.session.commit()
      except Exception as e:
          error_in_insert = True
          print(f'Exception "{e}" in create_venue_submission()')
          db.session.rollback()
      finally:
          db.session.close()

      if not error_in_insert:
          flash('Venue ' + request.form['name'] + ' was successfully listed!')
          return redirect(url_for('index'))
      else:
          flash('An error occurred. Venue ' + name + ' could not be listed.')
          print("Error in create_venue_submission()")
          abort(500)

@app.route('/venues/<venue_id>/delete', methods=['GET'])
def delete_venue(venue_id):
  # COMPLETE: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  venue = Venue.query.get(venue_id)
  if not venue:
      return redirect(url_for('index'))
  else:
      error_on_delete = False
      venue_name = venue.name
      try:
          db.session.delete(venue)
          db.session.commit()
      except:
          error_on_delete = True
          db.session.rollback()
      finally:
          db.session.close()
      if error_on_delete:
          flash(f'An error occurred deleting venue {venue_name}.')
          print("Error in delete_venue()")
          abort(500)
      else:
          # flash(f'Successfully removed venue {venue_name}')
          # return redirect(url_for('venues'))
          return jsonify({
              'deleted': True,
              'url': url_for('venues')
          })

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # COMPLETE: replace with real data returned from querying the database
  artists = Artist.query.order_by(Artist.name).all()  # Sort alphabetically

  data = []
  for artist in artists:
      data.append({
          "id": artist.id,
          "name": artist.name
      })
  # data=[{
  #   "id": 4,
  #   "name": "Guns N Petals",
  # }, {
  #   "id": 5,
  #   "name": "Matt Quevedo",
  # }, {
  #   "id": 6,
  #   "name": "The Wild Sax Band",
  # }]
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # COMPLETE: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  # Most of code is from search_venues()
  search_term = request.form.get('search_term', '').strip()
  artists = Artist.query.filter(Artist.name.ilike('%' + search_term + '%')).all()   # Wildcards search before and after
  artist_list = []
  now = datetime.now()
  for artist in artists:
      artist_shows = Show.query.filter_by(artist_id=artist.id).all()
      num_upcoming = 0
      for show in artist_shows:
          if show.start_time > now:
              num_upcoming += 1

      artist_list.append({
          "id": artist.id,
          "name": artist.name,
          "num_upcoming_shows": num_upcoming 
      })

  response = {
      "count": len(artists),
      "data": artist_list
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # COMPLETE: replace with real venue data from the venues table, using venue_id
  artist = Artist.query.get(artist_id)  
  if not artist:
      return redirect(url_for('index'))
  else:
      genres = [ genre.name for genre in artist.genres ] 
      past_shows = []
      past_shows_count = 0
      upcoming_shows = []
      upcoming_shows_count = 0
      now = datetime.now()
      for show in artist.shows:
          if show.start_time > now:
              upcoming_shows_count += 1
              upcoming_shows.append({
                  "venue_id": show.venue_id,
                  "venue_name": show.venue.name,
                  "venue_image_link": show.venue.image_link,
                  "start_time": format_datetime(str(show.start_time))
              })
          if show.start_time < now:
              past_shows_count += 1
              past_shows.append({
                  "venue_id": show.venue_id,
                  "venue_name": show.venue.name,
                  "venue_image_link": show.venue.image_link,
                  "start_time": format_datetime(str(show.start_time))
              })

      data = {
          "id": artist_id,
          "name": artist.name,
          "genres": genres,
          "city": artist.city,
          "state": artist.state,
          "phone": (artist.phone[:3] + '-' + artist.phone[3:6] + '-' + artist.phone[6:]),
          "website": artist.website,
          "facebook_link": artist.facebook_link,
          "seeking_venue": artist.seeking_venue,
          "seeking_description": artist.seeking_description,
          "image_link": artist.image_link,
          "past_shows": past_shows,
          "past_shows_count": past_shows_count,
          "upcoming_shows": upcoming_shows,
          "upcoming_shows_count": upcoming_shows_count
      }
  # data1={
  #   "id": 4,
  #   "name": "Guns N Petals",
  #   "genres": ["Rock n Roll"],
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "phone": "326-123-5000",
  #   "website": "https://www.gunsnpetalsband.com",
  #   "facebook_link": "https://www.facebook.com/GunsNPetals",
  #   "seeking_venue": True,
  #   "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
  #   "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
  #   "past_shows": [{
  #     "venue_id": 1,
  #     "venue_name": "The Musical Hop",
  #     "venue_image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
  #     "start_time": "2019-05-21T21:30:00.000Z"
  #   }],
  #   "upcoming_shows": [],
  #   "past_shows_count": 1,
  #   "upcoming_shows_count": 0,
  # }
  # data2={
  #   "id": 5,
  #   "name": "Matt Quevedo",
  #   "genres": ["Jazz"],
  #   "city": "New York",
  #   "state": "NY",
  #   "phone": "300-400-5000",
  #   "facebook_link": "https://www.facebook.com/mattquevedo923251523",
  #   "seeking_venue": False,
  #   "image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
  #   "past_shows": [{
  #     "venue_id": 3,
  #     "venue_name": "Park Square Live Music & Coffee",
  #     "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
  #     "start_time": "2019-06-15T23:00:00.000Z"
  #   }],
  #   "upcoming_shows": [],
  #   "past_shows_count": 1,
  #   "upcoming_shows_count": 0,
  # }
  # data3={
  #   "id": 6,
  #   "name": "The Wild Sax Band",
  #   "genres": ["Jazz", "Classical"],
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "phone": "432-325-5432",
  #   "seeking_venue": False,
  #   "image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #   "past_shows": [],
  #   "upcoming_shows": [{
  #     "venue_id": 3,
  #     "venue_name": "Park Square Live Music & Coffee",
  #     "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
  #     "start_time": "2035-04-01T20:00:00.000Z"
  #   }, {
  #     "venue_id": 3,
  #     "venue_name": "Park Square Live Music & Coffee",
  #     "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
  #     "start_time": "2035-04-08T20:00:00.000Z"
  #   }, {
  #     "venue_id": 3,
  #     "venue_name": "Park Square Live Music & Coffee",
  #     "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
  #     "start_time": "2035-04-15T20:00:00.000Z"
  #   }],
  #   "past_shows_count": 0,
  #   "upcoming_shows_count": 3,
  # }
  # data = list(filter(lambda d: d['id'] == artist_id, [data1, data2, data3]))[0]
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  # Taken mostly from edit_venue()
  artist = Artist.query.get(artist_id) 
  if not artist:
      return redirect(url_for('index'))
  else:
      form = ArtistForm(obj=artist)
  genres = [ genre.name for genre in artist.genres ]
  artist = {
      "id": artist_id,
      "name": artist.name,
      "genres": genres,
      "city": artist.city,
      "state": artist.state,
      "phone": (artist.phone[:3] + '-' + artist.phone[3:6] + '-' + artist.phone[6:]),
      "website": artist.website,
      "facebook_link": artist.facebook_link,
      "seeking_venue": artist.seeking_venue,
      "seeking_description": artist.seeking_description,
      "image_link": artist.image_link
  }
  # artist={
  #   "id": 4,
  #   "name": "Guns N Petals",
  #   "genres": ["Rock n Roll"],
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "phone": "326-123-5000",
  #   "website": "https://www.gunsnpetalsband.com",
  #   "facebook_link": "https://www.facebook.com/GunsNPetals",
  #   "seeking_venue": True,
  #   "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
  #   "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  # }
  # COMPLETE: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # COMPLETE: take values from the form submitted, and update existing
  # Much of this code from edit_venue_submission()
  form = ArtistForm()
  name = form.name.data.strip()
  city = form.city.data.strip()
  state = form.state.data
  phone = form.phone.data
  phone = re.sub('\D', '', phone) # e.g. (819) 392-1234 --> 8193921234
  genres = form.genres.data                   # ['Alternative', 'Classical', 'Country']
  seeking_venue = True if form.seeking_venue.data == 'Yes' else False
  seeking_description = form.seeking_description.data.strip()
  image_link = form.image_link.data.strip()
  website = form.website.data.strip()
  facebook_link = form.facebook_link.data.strip()
  
  if not form.validate():
    flash(form.errors)
    return redirect(url_for('edit_artist_submission', artist_id=artist_id))

  else:
      error_in_update = False
      try:
          artist = Artist.query.get(artist_id)
          artist.name = name
          artist.city = city
          artist.state = state
          artist.phone = phone
          artist.seeking_venue = seeking_venue
          artist.seeking_description = seeking_description
          artist.image_link = image_link
          artist.website = website
          artist.facebook_link = facebook_link
          artist.genres = []
          
          for genre in genres:
              fetch_genre = Genre.query.filter_by(name=genre).one_or_none()  # Throws an exception if more than one returned, returns None if none
              if fetch_genre:
                  artist.genres.append(fetch_genre)

              else:
                  new_genre = Genre(name=genre)
                  db.session.add(new_genre)
                  artist.genres.append(new_genre)  # Create a new Genre item and append it
          db.session.commit()
      except Exception as e:
          error_in_update = True
          print(f'Exception "{e}" in edit_artist_submission()')
          db.session.rollback()
      finally:
          db.session.close()

      if not error_in_update:
          # on successful db update, flash success
          flash('Artist ' + request.form['name'] + ' was successfully updated!')
          return redirect(url_for('show_artist', artist_id=artist_id))
      else:
          flash('An error occurred. Artist ' + name + ' could not be updated.')
          print("Error in edit_artist_submission()")
          abort(500)


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id) 
  if not venue:
      return redirect(url_for('index'))
  else:
      form = VenueForm(obj=venue)
  genres = [ genre.name for genre in venue.genres ]
  venue = {
    "id": venue_id,
    "name": venue.name,
    "genres": genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    # Put the dashes back into phone number
    "phone": (venue.phone[:3] + '-' + venue.phone[3:6] + '-' + venue.phone[6:]),
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link
  }
  # venue={
  #   "id": 1,
  #   "name": "The Musical Hop",
  #   "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
  #   "address": "1015 Folsom Street",
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "phone": "123-123-1234",
  #   "website": "https://www.themusicalhop.com",
  #   "facebook_link": "https://www.facebook.com/TheMusicalHop",
  #   "seeking_talent": True,
  #   "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
  #   "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  # }
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # COMPLETE: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  form = VenueForm()
  name = form.name.data.strip()
  city = form.city.data.strip()
  state = form.state.data
  address = form.address.data.strip()
  phone = form.phone.data
  phone = re.sub('\D', '', phone) # e.g. (819) 392-1234 --> 8193921234
  genres = form.genres.data                   # ['Alternative', 'Classical', 'Country']
  seeking_talent = True if form.seeking_talent.data == 'Yes' else False
  seeking_description = form.seeking_description.data.strip()
  image_link = form.image_link.data.strip()
  website = form.website.data.strip()
  facebook_link = form.facebook_link.data.strip()
  if not form.validate():
      flash( form.errors )
      return redirect(url_for('edit_venue_submission', venue_id=venue_id))

  else:
      error_in_update = False
      try:
          venue = Venue.query.get(venue_id)
          venue.name = name
          venue.city = city
          venue.state = state
          venue.address = address
          venue.phone = phone

          venue.seeking_talent = seeking_talent
          venue.seeking_description = seeking_description
          venue.image_link = image_link
          venue.website = website
          venue.facebook_link = facebook_link
          venue.genres = []

          for genre in genres:
              fetch_genre = Genre.query.filter_by(name=genre).one_or_none()  # Throws an exception if more than one returned, returns None if none
              if fetch_genre:
                  venue.genres.append(fetch_genre)

              else:
                  new_genre = Genre(name=genre)
                  db.session.add(new_genre)
                  venue.genres.append(new_genre) 
          db.session.commit()
      except Exception as e:
          error_in_update = True
          print(f'Exception "{e}" in edit_venue_submission()')
          db.session.rollback()
      finally:
          db.session.close()

      if not error_in_update:
          # on successful db update, flash success
          flash('Venue ' + request.form['name'] + ' was successfully updated!')
          return redirect(url_for('show_venue', venue_id=venue_id))
      else:
          flash('An error occurred. Venue ' + name + ' could not be updated.')
          print("Error in edit_venue_submission()")
          abort(500)

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # COMPLETE: insert form data as a new Venue record in the db, instead
  # COMPLETE: modify data to be the data object returned from db insertion
  # on successful db insert, flash success
  # Much of this code is similar to create_venue view
  form = ArtistForm()
  name = form.name.data.strip()
  city = form.city.data.strip()
  state = form.state.data
  phone = form.phone.data
  phone = re.sub('\D', '', phone) # e.g. (819) 392-1234 --> 8193921234
  genres = form.genres.data                   # ['Alternative', 'Classical', 'Country']
  seeking_venue = True if form.seeking_venue.data == 'Yes' else False
  seeking_description = form.seeking_description.data.strip()
  image_link = form.image_link.data.strip()
  website = form.website.data.strip()
  facebook_link = form.facebook_link.data.strip()
  
  # Redirect back to form if errors in form validation
  if not form.validate():
      flash( form.errors )
      return redirect(url_for('create_artist_submission'))

  else:
      error_in_insert = False

      # Insert form data into DB
      try:
          # creates the new artist with all fields but not genre yet
          new_artist = Artist(name=name, city=city, state=state, phone=phone, \
              seeking_venue=seeking_venue, seeking_description=seeking_description, image_link=image_link, \
              website=website, facebook_link=facebook_link)
          # genres can't take a list of strings, it needs to be assigned to db objects
          # genres from the form is like: ['Alternative', 'Classical', 'Country']
          for genre in genres:
              # fetch_genre = session.query(Genre).filter_by(name=genre).one_or_none()  # Throws an exception if more than one returned, returns None if none
              fetch_genre = Genre.query.filter_by(name=genre).one_or_none()  # Throws an exception if more than one returned, returns None if none
              if fetch_genre:
                  # if found a genre, append it to the list
                  new_artist.genres.append(fetch_genre)

              else:
                  # fetch_genre was None. It's not created yet, so create it
                  new_genre = Genre(name=genre)
                  db.session.add(new_genre)
                  new_artist.genres.append(new_genre)  # Create a new Genre item and append it

          db.session.add(new_artist)
          db.session.commit()
      except Exception as e:
          error_in_insert = True
          print(f'Exception "{e}" in create_artist_submission()')
          db.session.rollback()
      finally:
          db.session.close()

      if not error_in_insert:
          # on successful db insert, flash success
          flash('Artist ' + request.form['name'] + ' was successfully listed!')
          return redirect(url_for('index'))
      else:
          flash('An error occurred. Artist ' + name + ' could not be listed.')
          print("Error in create_artist_submission()")
          abort(500)

# Create delete_artist (much like delete_venue)
@app.route('/artists/<artist_id>/delete', methods=['GET'])
def delete_artist(artist_id):
    artist = Artist.query.get(artist_id)
    if not artist:
        return redirect(url_for('index'))
    else:
        error_on_delete = False
        artist_name = artist.name
        try:
            db.session.delete(artist)
            db.session.commit()
        except:
            error_on_delete = True
            db.session.rollback()
        finally:
            db.session.close()
        if error_on_delete:
            flash(f'An error occurred deleting artist {artist_name}.')
            print("Error in delete_artist()")
            abort(500)
        else:
            return jsonify({
                'deleted': True,
                'url': url_for('artists')
            })
#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # COMPLETE: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data = []
  shows = Show.query.all()
  
  for show in shows:
      data.append({
          "venue_id": show.venue.id,
          "venue_name": show.venue.name,
          "artist_id": show.artist.id,
          "artist_name": show.artist.name,
          "artist_image_link": show.artist.image_link,
          "start_time": format_datetime(str(show.start_time))
      })

  # data=[{
  #   "venue_id": 1,
  #   "venue_name": "The Musical Hop",
  #   "artist_id": 4,
  #   "artist_name": "Guns N Petals",
  #   "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
  #   "start_time": "2019-05-21T21:30:00.000Z"
  # }, {
  #   "venue_id": 3,
  #   "venue_name": "Park Square Live Music & Coffee",
  #   "artist_id": 5,
  #   "artist_name": "Matt Quevedo",
  #   "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
  #   "start_time": "2019-06-15T23:00:00.000Z"
  # }, {
  #   "venue_id": 3,
  #   "venue_name": "Park Square Live Music & Coffee",
  #   "artist_id": 6,
  #   "artist_name": "The Wild Sax Band",
  #   "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #   "start_time": "2035-04-01T20:00:00.000Z"
  # }, {
  #   "venue_id": 3,
  #   "venue_name": "Park Square Live Music & Coffee",
  #   "artist_id": 6,
  #   "artist_name": "The Wild Sax Band",
  #   "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #   "start_time": "2035-04-08T20:00:00.000Z"
  # }, {
  #   "venue_id": 3,
  #   "venue_name": "Park Square Live Music & Coffee",
  #   "artist_id": 6,
  #   "artist_name": "The Wild Sax Band",
  #   "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #   "start_time": "2035-04-15T20:00:00.000Z"
  # }]
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  form = ShowForm()
  artist_id = form.artist_id.data.strip()
  venue_id = form.venue_id.data.strip()
  start_time = form.start_time.data

  error_in_insert = False
  
  try:
      new_show = Show(start_time=start_time, artist_id=artist_id, venue_id=venue_id)
      db.session.add(new_show)
      db.session.commit()
  except:
      error_in_insert = True
      print(f'Exception "{e}" in create_show_submission()')
      db.session.rollback()
  finally:
      db.session.close()

  if error_in_insert:
      flash(f'An error occurred.  Show could not be listed.')
      print("Error in create_show_submission()")
  else:
      flash('Show was successfully listed!')
  
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''

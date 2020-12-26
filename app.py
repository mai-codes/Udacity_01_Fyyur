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
  search_term = request.form.get('search_term', '')
  search_result = db.session.query(Venue).filter(Venue.name.ilike(f'%{search_term}%')).all()
  data = []

  for result in search_result:
    data.append({
      "id": result.id,
      "name": result.name,
      "num_upcoming_shows": len(db.session.query(Show).filter(Show.venue_id == result.id).filter(Show.start_time > datetime.now()).all()),
    })
  
  response={
    "count": len(search_result),
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # COMPLETE: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.get(venue_id)

  if not venue: 
    return render_template('errors/404.html')

  upcoming_shows_query = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time>datetime.now()).all()
  upcoming_shows = []

  past_shows_query = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time<datetime.now()).all()
  past_shows = []

  for show in past_shows_query:
    past_shows.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  for show in upcoming_shows_query:
    upcoming_shows.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")    
    })

  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }

  return render_template('pages/show_venue.html', venue=data)
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
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # COMPLETE: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  # Most of code is from search_venues()
  artist_query = db.session.query(Artist).get(artist_id)

  if not artist_query: 
    return render_template('errors/404.html')

  past_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>datetime.now()).all()
  past_shows = []

  for show in past_shows_query:
    past_shows.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_image_link": show.venue.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  upcoming_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>datetime.now()).all()
  upcoming_shows = []

  for show in upcoming_shows_query:
    upcoming_shows.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_image_link": show.venue.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })


  data = {
    "id": artist_query.id,
    "name": artist_query.name,
    "genres": artist_query.genres,
    "city": artist_query.city,
    "state": artist_query.state,
    "phone": artist_query.phone,
    "website": artist_query.website,
    "facebook_link": artist_query.facebook_link,
    "seeking_venue": artist_query.seeking_venue,
    "seeking_description": artist_query.seeking_description,
    "image_link": artist_query.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }

  return render_template('pages/show_artist.html', artist=data)

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
  shows_query = db.session.query(Show).join(Artist).join(Venue).all()

  data = []
  for show in shows_query: 
    data.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_id": show.artist_id,
      "artist_name": show.artist.name, 
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

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

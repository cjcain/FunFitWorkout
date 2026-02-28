# WORKOUT SELECTION APP:

I started using FunFitLand in 2024 when I bought my Meta Quest 3 headset.
There was only a few workouts back then, but the workouts and music were
so fun, that I still use it almost everyday.

Now, FunFitLand has so many workouts I have a hard time trying to decide
what workouts I want to use everyday.

I love a variety and wanted to have a way to select a random set of
workouts (from my favorites) and prioritize workouts I have not done
for a long time. Hopefully this capability will be added to the app
so I don't have to use this app.

Since this is a separate app, it is a bit of manual process to actually
search for each of the randomly selected workouts, but it is not difficult
and works for me.


# REQUIREMENTS:

  - Python 3     - free to download from https://www.python.org/downloads/
  - workouts.py  - the application
  - workouts.csv - the list of workouts to choose from
  - FunFitLand app - https://www.funfitland.com/

  I have tested this on Windows & Linux, but should work on any system
  that supports Python 3.


# RUNNING THE APP:

Start the app with: python3 workouts.py

A window will appear so the user can select the workout type, level, and
time the workout set should use.

1. Workout type: groove, combat or flow

    All workouts will use the selected type

2. Minimum and Maximum level: Light / Medium / Intense

    The workout level has used to define the range of workout intensity that
    is desired. It has a minimum and maximum. The default is to allow all
    levels (from Light to Intense). It will select at least one workout at
    each level (assuming there is enough time).
    Example: For an easy workout set you can set Min and Max to Light and
    then all workouts would be Light.

3. Target duration (in minutes)

    This is the desired minimum workout set duration. Since it is hard to find
    a perfect set of workouts for a target duration some of the sets will be
    a few minutes longer than the target duration.


After selecting the desired options, the user should click the "Generate Workout"
button. That will calculate a set of workouts meeting the chriteria.

Example output:

    Selected Workouts: (groove)
      - Echos of Home (13 min, Light, Folk)
      - Chill Time (13 min, Medium, HipHop)
      - Future Space (17 min, Intense, Pop)

      Duration: 43 min (13 min @ Light / 13 min @ Medium / 17 min @ Intense)
      Average difficulty: 2.00 (Medium)

The user can get different workout sets by pressing the "Generate Workout" button.
Once the user sees a set they like, they can press the "Approve" button.

The app will then update the "last used date" for the selected workouts to today.
This prevents the the same workouts from coming up frequently (as I said, I
prefer a variety!)


# SELECTING THE WORKOUTS IN FUNFITLAND APP:

1. From the main menu click on the WORKOUTS button on the bottom.
2. On the upper left, click the desired workout type (Goove, Combat, Flow)
3. On the top middle line (with magnifying glass) and then type in part of
   the first workout name. It will then show list of matching workouts.
4. Click on workout tile and press the Start button in bottom middle.
5. Do the workout
6. Go back to step 3 for the next workout


# FILE DESCRIPTIONS:
  workouts.py - The Python 3 application script
  workouts.csv - List of workouts that the user would like to use (favorites)
                 The initial file will contain all FunFitLand workouts as of
                 when the file was uploaded.
                 The user can edit this text file and remove the line containing
                 any workouts they do not want to use.
  FunFitLandWorkouts_all.csv - List of all FunFitLand workouts as of 28-Feb-2026
                 File is initially the same as workouts.csv but included so the user
                 can modify workouts.csv, but still go back to original if desired.

  The following files will get created after accepting a workout set.
    workouts_dates.json - List of workouts and date they were last used
    workouts_lasttype.txt - internal file to keep track of last workout
    workouts_log.csv - List of workouts and when they were accepted (history)

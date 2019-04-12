#!/usr/bin/env python2
"""
ExtinctioRecallTrainingTask.py
Display images from a specified folder and present them to the subject, rating the images on given scales.
Also have rest and "dummy" runs and present mood ratings to the subject in between.

Created 1/11/19 by DJ based on ExtinctionRecallAndVasTask.py.
Updated 1/22/19 by DJ - modified "range" calls to make compatible with python3
Updated 2/21/19 by DJ - changed timing, added MSI, moved stimuli, changed names to CSplus-1/2, randomize Q order for each run but not each group
Updated 2/25/19 by DJ - changed timing, added visible tick marks to VAS
Updated 3/25/19 by GF - added second run and set of prompts
Updated 4/12/19 by DJ - no processing at end of task, changed log filename
"""

# Import packages
from psychopy import visual, core, gui, data, event, logging 
from psychopy.tools.filetools import fromFile, toFile # saving and loading parameter files
import time as ts, numpy as np # for timing and array operations
import os, glob # for file manipulation
import BasicPromptTools # for loading/presenting prompts and questions
import random # for randomization of trials
import RatingScales # for VAS sliding scale

# ====================== #
# ===== PARAMETERS ===== #
# ====================== #
# Save the parameters declared below?
saveParams = True;
newParamsFilename = 'ExtinctionRecallTrainingParams.psydat'

# Declare primary task parameters.
params = {
# Declare experiment flow parameters
    'nTrialsPerBlock': 2,   # number of trials in a block
    'nBlocksPerGroup': 2,   # number of blocks in a group (should match number of face VAS questions)
    'nGroupsPerRun': 1,     # number times this "group" pattern should repeat
# Declare timing parameters
    'tStartup': 6.,        # 3., #time displaying instructions while waiting for scanner to reach steady-state
    'tBaseline': 6.,       # 2., # pause time before starting first stimulus
    'tPreBlockPrompt': 5.,  # duration of prompt before each block
    'tStimMin': 2.,         # min duration of stimulus (in seconds)
    'tStimMax': 4.,         # max duration of stimulus (in seconds)
    'questionDur': 2.5,     # duration of the image rating (in seconds)
    'tMsiMin': 0.5,         # min time between when one stimulus disappears and the next appears (in seconds)
    'tMsiMax': 3.5,         # max time between when one stimulus disappears and the next appears (in seconds)
    'tIsiMin': 0.5,         # min time between when one stimulus disappears and the next appears (in seconds)
    'tIsiMax': 7.,          # max time between when one stimulus disappears and the next appears (in seconds)
    'fixCrossDur': 6.,     # 1.,# duration of cross fixation before each run
# Declare stimulus and response parameters
    'preppedKey': 'y',      # key from experimenter that says scanner is ready
    'triggerKey': '5',      # key from scanner that says scan is starting
    'imageDir': 'Faces/',   # directory containing image stimluli
    'imageNames': ['ER3_trainingface1.jpg','ER3_trainingface2.jpg'],   # images will be selected randomly (without replacement) from this list of files in imageDir.
# declare prompt files
    'skipPrompts': False,   # go right to the scanner-wait page
    'promptFile1': 'Prompts/ERTrainingPrompts1.txt', # Name of text file containing prompts shown before the Mood VAS practice 
    'promptFile2': "Prompts/ERTrainingPrompts2.txt", # text file containing prompts shown before the image ratings practice
    'promptFile3': 'Prompts/ERTrainingPrompts3.txt', # text file containing prompts to make sure participant understands task
    'PreVasMsg': "Let's do some rating scales.", # text (not file) shown BEFORE each VAS except the final one
    'PreFinalVasMsg': "We're done!", # text shown before final VAS
# declare VAS info
    'faceQuestionFile': 'Questions/ERFaceRatingScales.txt', # Name of text file containing image Q&As
    'moodQuestionFile1': 'Questions/ERVas1RatingScales.txt', # Name of text file containing mood Q&As presented before sound check
    'questionDownKey': '4', # red on fORP
    'questionUpKey':'2',    # yellow on fORP
    'questionSelectKey':'3', # green on fORP
    'questionSelectAdvances': False,
# parallel port parameters
    'sendPortEvents': True, # send event markers to biopac computer via parallel port
    'portAddress': 0xD050,  # 0x0378, # address of parallel port
    'codeBaseline': 31,     # parallel port code for baseline period (make sure it's greater than nBlocks*2*len(imageNames)!)
    'codeVas': 32,          # parallel port code for mood ratings (make sure it's greater than nBlocks*2*len(imageNames)!)
# declare display parameters
    'fullScreen': True,     # run in full screen mode?
    'screenToShow': 0,      # display on primary screen (0) or secondary (1)?
    'fixCrossSize': 50,     # size of cross, in pixels
    'fixCrossPos': [0,0],   # (x,y) pos of fixation cross displayed before each stimulus (for gaze drift correction)
    'faceHeight': 2.,       # in norm units: 2 = height of screen
    'screenColor':(120,120,120),    # (120,120,120) in rgb255 space: (r,g,b) all between 0 and 255
    'textColor': (-1,-1,-1),  # color of text outside of VAS
    'moodVasScreenColor': (110,110,200),  # background behind mood VAS and its pre-VAS prompt. Ideally luminance-matched to screen color via luminance meter/app, else keep in mind gamma correction Y = 0.2126 * R + 0.7152 * G + 0.0722 * B
    'vasTextColor': (-1,-1,-1), # color of text in both VAS types (-1,-1,-1) = black
    'vasMarkerSize': 0.1,   # in norm units (2 = whole screen)
    'vasLabelYDist': 0.1,   # distance below line that VAS label/option text should be, in norm units
    'screenRes': (1024,768) # screen resolution (hard-coded because AppKit isn't available on PCs)
}

# save parameters
if saveParams:
    dlgResult = gui.fileSaveDlg(prompt='Save Params...',initFilePath = os.getcwd() + '/Params', initFileName = newParamsFilename,
        allowed="PSYDAT files (*.psydat);;All files (*.*)")
    newParamsFilename = dlgResult
    if newParamsFilename is None: # keep going, but don't save
        saveParams = False
    else:
        toFile(newParamsFilename, params) # save it!

# ========================== #
# ===== SET UP LOGGING ===== #
# ========================== #
scriptName = os.path.basename(__file__)
scriptName = os.path.splitext(scriptName)[0] # remove extension
try: # try to get a previous parameters file
    expInfo = fromFile('%s-lastExpInfo.psydat'%scriptName)
    expInfo['session'] +=1 # automatically increment session number
    expInfo['paramsFile'] = [expInfo['paramsFile'],'Load...']
except: # if not there then use a default set
    expInfo = {
        'subject':'1', 
        'session': 1, 
        'skipPrompts':False, 
        'sendPortEvents': True,
        'paramsFile':['DEFAULT','Load...']}
# overwrite params struct if you just saved a new parameter set
if saveParams:
    expInfo['paramsFile'] = [newParamsFilename,'Load...']

#present a dialogue to change select params
dlg = gui.DlgFromDict(expInfo, title=scriptName, order=['subject','session','skipPrompts','sendPortEvents','paramsFile'])
if not dlg.OK:
    core.quit() # the user hit cancel, so exit

expInfo['paramsFile'] = ''.join(expInfo['paramsFile']) # convert from list of characters to string
# find parameter file
if expInfo['paramsFile'] == 'Load...':
    dlgResult = gui.fileOpenDlg(prompt='Select parameters file',tryFilePath=os.getcwd(),
        allowed="PSYDAT files (*.psydat);;All files (*.*)")
    expInfo['paramsFile'] = dlgResult[0]
# load parameter file
if expInfo['paramsFile'] not in ['DEFAULT', None]: # otherwise, just use defaults.
    # load params file
    print(expInfo)
    params = fromFile(expInfo['paramsFile'])


# transfer experimental flow items from expInfo (gui input) to params (logged parameters)
for flowItem in ['skipPrompts','sendPortEvents']:
    params[flowItem] = expInfo[flowItem]


# print params to Output
print('params = {')
for key in sorted(params.keys()):
    print("   '%s': %s"%(key,params[key])) # print each value as-is (no quotes)
print('}')
    
# save experimental info
toFile('%s-lastExpInfo.psydat'%scriptName, expInfo)#save params to file for next time

#make a log file to save parameter/event  data
dateStr = ts.strftime("%m-%d-%Y", ts.localtime()) # add the current time
logFilename = 'Logs/ER3Training_%s-%d_%s.log'%(expInfo['subject'], expInfo['session'], dateStr) # log filename
logging.LogFile((logFilename), level=logging.INFO)#, mode='w') # w=overwrite
logging.log(level=logging.INFO, msg='---START PARAMETERS---')
logging.log(level=logging.INFO, msg='filename: %s'%logFilename)
logging.log(level=logging.INFO, msg='subject: %s'%expInfo['subject'])
logging.log(level=logging.INFO, msg='session: %s'%expInfo['session'])
logging.log(level=logging.INFO, msg='date: %s'%dateStr)
# log everything in the params struct
for key in sorted(params.keys()): # in alphabetical order
    logging.log(level=logging.INFO, msg='%s: %s'%(key,params[key])) # log each parameter

logging.log(level=logging.INFO, msg='---END PARAMETERS---')


# ========================== #
# == SET UP PARALLEL PORT == #
# ========================== #

if params['sendPortEvents']:
    from psychopy import parallel
    port = parallel.ParallelPort(address=params['portAddress'])
    port.setData(0) # initialize to all zeros
else:
    print("Parallel port not used.")
    

# ========================== #
# ===== SET UP STIMULI ===== #
# ========================== #

# Initialize deadline for displaying next frame
tNextFlip = [0.0] # put in a list to make it mutable (weird quirk of python variables) 

#create clocks and window
globalClock = core.Clock()#to keep track of time
trialClock = core.Clock()#to keep track of time
win = visual.Window(params['screenRes'], fullscr=params['fullScreen'], allowGUI=False, monitor='testMonitor', screen=params['screenToShow'], units='deg', name='win',color=params['screenColor'],colorSpace='rgb255')
# create fixation cross
fCS = params['fixCrossSize'] # size (for brevity)
fCP = params['fixCrossPos'] # position (for brevity)
lineWidth = int(params['fixCrossSize']/3)
fixation = visual.ShapeStim(win,lineColor=params['textColor'],lineWidth=lineWidth,vertices=((fCP[0]-fCS/2,fCP[1]),(fCP[0]+fCS/2,fCP[1]),(fCP[0],fCP[1]),(fCP[0],fCP[1]+fCS/2),(fCP[0],fCP[1]-fCS/2)),units='pix',closeShape=False,name='fixCross');
duration = params['fixCrossDur'] # duration (for brevity)

# create text stimuli
message1 = visual.TextStim(win, pos=[0,+.4], wrapWidth=1.5, color=params['textColor'], alignHoriz='center', name='topMsg', text="aaa",units='norm')
message2 = visual.TextStim(win, pos=[0,-.4], wrapWidth=1.5, color=params['textColor'], alignHoriz='center', name='bottomMsg', text="bbb",units='norm')

# get stimulus files
allImages = [params['imageDir'] + name for name in params['imageNames']] # assemble filenames: <imageDir>/<imageNames>.
allNames = ['CSplus-1','CSplus-2'] # in main task this is CSplusX...
allCodes = list(range(1,len(allImages)+1)) # codes sent to parallel port when each image is displayed

# initialize main image stimulus
imageName = allImages[0] # initialize with first image
stimImage = visual.ImageStim(win, pos=[0.,0.], name='ImageStimulus',image=imageName, units='norm')
aspectRatio = float(stimImage.size[0])/stimImage.size[1];
stimImage.size = (aspectRatio*params['faceHeight'], params['faceHeight']); # to maintain aspect ratio

# read prompts, questions and answers from text files
[topPrompts1,bottomPrompts1] = BasicPromptTools.ParsePromptFile(params['promptFile1'])
print('%d prompts loaded from %s'%(len(topPrompts1),params['promptFile1']))

[topPrompts2,bottomPrompts2] = BasicPromptTools.ParsePromptFile(params['promptFile2'])
print('%d prompts loaded from %s'%(len(topPrompts2),params['promptFile2']))

[topPrompts3,bottomPrompts3] = BasicPromptTools.ParsePromptFile(params['promptFile3'])
print('%d prompts loaded from %s'%(len(topPrompts3),params['promptFile3']))

[questions,options,answers] = BasicPromptTools.ParseQuestionFile(params['faceQuestionFile'])
print('%d questions loaded from %s'%(len(questions),params['faceQuestionFile']))

[questions_vas1,options_vas1,answers_vas1] = BasicPromptTools.ParseQuestionFile(params['moodQuestionFile1'])
print('%d questions loaded from %s'%(len(questions_vas1),params['moodQuestionFile1']))

# declare order of blocks for later randomization
blockOrder = list(range(params['nBlocksPerGroup']))


# ============================ #
# ======= SUBFUNCTIONS ======= #
# ============================ #

# increment time of next window flip
def AddToFlipTime(tIncrement=1.0):
    tNextFlip[0] += tIncrement

# flip window as soon as possible
def SetFlipTimeToNow():
    tNextFlip[0] = globalClock.getTime()

def WaitForFlipTime():
    while (globalClock.getTime()<tNextFlip[0]):
        keyList = event.getKeys()
        # Check for escape characters
        for key in keyList:
            if key in ['q','escape']:
                CoolDown()

# Send parallel port event
def SetPortData(data):
    if params['sendPortEvents']:
        logging.log(level=logging.EXP,msg='set port %s to %d'%(format(params['portAddress'],'#04x'),data))
        port.setData(data)
    else:
        print('Port event: %d'%data)


# Wait for scanner, then display a fixation cross
def WaitForScanner():
    # wait for experimenter
    message1.setText("Experimenter, is the scanner prepared?")
    message2.setText("(Press '%c' when it is.)"%params['preppedKey'].upper())
    message1.draw()
    message2.draw()
    win.logOnFlip(level=logging.EXP, msg='Display WaitingForPrep')
    win.flip()
    keyList = event.waitKeys(keyList=[params['preppedKey'],'q','escape'])
    # Check for escape characters
    for key in keyList:
        if key in ['q','escape']:
            CoolDown()
    
    # wait for scanner
    message1.setText("Waiting for scanner to start...")
    message2.setText("(Press '%c' to override.)"%params['triggerKey'].upper())
    message1.draw()
    message2.draw()
    win.logOnFlip(level=logging.EXP, msg='Display WaitingForScanner')
    win.flip()
    keyList = event.waitKeys(keyList=[params['triggerKey'],'q','escape'])
    SetFlipTimeToNow()
    # Check for escape characters
    for key in keyList:
        if key in ['q','escape']:
            CoolDown()

# Display the prompt before a block
def ShowPreBlockPrompt(question,iPrompt):
    # update messages and draw them
    message1.setText("In this block, when you see a face, answer:")
    message2.setText(question)
    message1.draw()
    message2.draw()
    # set up logging
    win.logOnFlip(level=logging.EXP, msg='Display PreBlockPrompt%d'%iPrompt)
    # wait until it's time
    WaitForFlipTime()
    # update display 
    win.flip()
    # Update next stim time
    AddToFlipTime(params['tPreBlockPrompt'])
    

# Display an image
def ShowImage(imageFile, stimDur=float('Inf'),imageName='image'):
    # display info to experimenter
    print('Showing Stimulus %s'%imageName) 
    
    # Draw image
    stimImage.setImage(imageFile)
    stimImage.draw()
    # Wait until it's time to display
    WaitForFlipTime()
    # log & flip window to display image
    win.logOnFlip(level=logging.EXP, msg='Display %s %s'%(imageFile,imageName))
    win.flip()
    # Update next stim time
    AddToFlipTime(stimDur) # add to tNextFlip[0]
    

# Run a set of visual analog scale (VAS) questions
def RunVas(questions,options,pos=(0.,-0.25),scaleTextPos=[0.,0.25],questionDur=params['questionDur'],isEndedByKeypress=params['questionSelectAdvances'],name='Vas'):
    
    # wait until it's time
    WaitForFlipTime()
    
    # Show questions and options
    [rating,decisionTime,choiceHistory] = RatingScales.ShowVAS(questions,options, win, questionDur=questionDur, \
        upKey=params['questionUpKey'], downKey=params['questionDownKey'], selectKey=params['questionSelectKey'],\
        isEndedByKeypress=isEndedByKeypress, textColor=params['vasTextColor'], name=name, pos=pos,\
        scaleTextPos=scaleTextPos, labelYPos=pos[1]-params['vasLabelYDist'], markerSize=params['vasMarkerSize'],\
        tickHeight=1,tickLabelWidth = 0.9)
    
    # Update next stim time
    if isEndedByKeypress:
        SetFlipTimeToNow() # no duration specified, so timing creep isn't an issue
    else:
        AddToFlipTime(questionDur*len(questions)) # add question duration * # of questions



def RunMoodVas(questions,options,name='MoodVas'):
    
    # Wait until it's time
    WaitForFlipTime()
    # Set screen color
    win.color = params['moodVasScreenColor']
    win.flip() # must flip twice for color change to take
    
    # display pre-VAS prompt
    if not params['skipPrompts']:
        BasicPromptTools.RunPrompts([params['PreVasMsg']],["Press any button to continue."],win,message1,message2)
    
    # Display this VAS
    win.callOnFlip(SetPortData,data=params['codeVas'])
    RunVas(questions,options,questionDur=float("inf"), isEndedByKeypress=True,name=name)
    
    # Set screen color back
    win.color = params['screenColor']
    win.flip() # flip so the color change 'takes' right away

def DoRun(allImages,allCodes,allNames):
    # wait for scanner
    WaitForScanner() # includes SetFlipTimeToNow
    # Log state of experiment
    logging.log(level=logging.EXP,msg='===== START RUN =====')
    
    # display fixation before first stimulus
    fixation.draw()
    win.callOnFlip(SetPortData,data=params['codeBaseline'])
    win.logOnFlip(level=logging.EXP, msg='Display Fixation')
    # wait until it's time to show screen
    WaitForFlipTime()
    # Update time of next stim
    AddToFlipTime(params['fixCrossDur']) # duration of cross before each run
    # show screen and update next flip time
    win.flip()
    AddToFlipTime(params['tBaseline'])
    
    # randomize order of blocks
    random.shuffle(blockOrder)
    
    # RUN GROUP OF BLOCKS
    for iGroup in range(params['nGroupsPerRun']):
        # Log state of experiment
        logging.log(level=logging.EXP,msg='==== START GROUP %d/%d ===='%(iGroup+1,params['nGroupsPerRun']))
        
        # RUN BLOCK
        for iBlock in range(params['nBlocksPerGroup']):
            
            # Log state of experiment
            logging.log(level=logging.EXP,msg='=== START BLOCK %d/%d TYPE %d ==='%(iBlock+1,params['nBlocksPerGroup'],blockOrder[iBlock]))
            
            # randomize order of images and codes the same way
            ziplist = list(zip(allImages, allCodes, allNames))
            random.shuffle(ziplist)
            allImages, allCodes, allNames = zip(*ziplist)
            
            # Display pre-block prompt
            ShowPreBlockPrompt(questions[blockOrder[iBlock]].upper(), blockOrder[iBlock])
            
            # RUN TRIAL
            for iTrial in range(params['nTrialsPerBlock']):
                # get randomized stim time
                stimDur = random.uniform(params['tStimMin'],params['tStimMax'])
                # display image
                portCode = len(allCodes)*(blockOrder[iBlock]) + allCodes[iTrial]
                win.callOnFlip(SetPortData,data=portCode)
                ShowImage(imageFile=allImages[iTrial],stimDur=stimDur,imageName=allNames[iTrial])
                
                # get randomized MSI (mid-stim interval)
                tMsi = random.uniform(params['tMsiMin'],params['tMsiMax'])
                # Display the fixation cross
                fixation.draw() # draw it
                win.logOnFlip(level=logging.EXP, msg='Display Fixation')
                win.callOnFlip(SetPortData,data=0)
                # VAS keeps control to the end, so no need to wait for flip time
                WaitForFlipTime()
                win.flip()
                AddToFlipTime(tMsi)
                
                # Display VAS
                portCode = len(allCodes)*(blockOrder[iBlock]+2) + allCodes[iTrial]
                win.callOnFlip(SetPortData,data=portCode)
                RunVas([questions[blockOrder[iBlock]]],[options[blockOrder[iBlock]]],name='ImageRating')
                
                # get randomized ISI
                tIsi = random.uniform(params['tIsiMin'],params['tIsiMax'])
                # Display Fixation Cross (ISI)
                if iTrial < (params['nTrialsPerBlock']-1):
                    # Display the fixation cross
                    fixation.draw() # draw it
                    win.logOnFlip(level=logging.EXP, msg='Display Fixation')
                    win.callOnFlip(SetPortData,data=0)
                    # VAS keeps control to the end, so no need to wait for flip time
                    win.flip()
                    AddToFlipTime(tIsi)
                    
            # Log state of experiment
            logging.log(level=logging.EXP,msg='=== END BLOCK %d/%d TYPE %d ==='%(iBlock+1,params['nBlocksPerGroup'],blockOrder[iBlock]))
            
        # Log state of experiment
        logging.log(level=logging.EXP,msg='==== END GROUP %d/%d ===='%(iGroup+1,params['nGroupsPerRun']))
    
    # Log state of experiment
    logging.log(level=logging.EXP,msg='===== END RUN =====')


# Handle end of a session
def CoolDown():
    
    # turn off auto-draw of image
    stimImage.autoDraw = False
    win.flip()
    
    # display cool-down message after processing log
    message1.setText("That's the end! We are ready to go in the scanner now.")
    message2.setText("Press 'q' or 'escape' to end the session.")
    win.logOnFlip(level=logging.EXP, msg='Display TheEnd')
    message1.draw()
    message2.draw()
    win.flip()
    thisKey = event.waitKeys(keyList=['q','escape'])
    
    # exit
    core.quit()


# === SET UP GLOBAL ESCAPE KEY === #
event.globalKeys.clear()
event.globalKeys.add(key='q', modifiers=['ctrl'], func=CoolDown)


# === MAIN EXPERIMENT === #

# log experiment start and set up
logging.log(level=logging.EXP, msg='---START EXPERIMENT---')

# ---Instructions
# display prompts
if not params['skipPrompts']:
    BasicPromptTools.RunPrompts(topPrompts1,bottomPrompts1,win,message1,message2)

# ---VAS
RunMoodVas(questions_vas1,options_vas1,name='PreRun1-')

# ---Instructions
# display prompts
if not params['skipPrompts']:
    BasicPromptTools.RunPrompts(topPrompts2,bottomPrompts2,win,message1,message2)

# ---Run 1
DoRun(allImages,allCodes,allNames)

# ---Instructions
# display prompts
if not params['skipPrompts']:
    BasicPromptTools.RunPrompts(topPrompts3,bottomPrompts3,win,message1,message2)

# ---Run 2
DoRun(allImages,allCodes,allNames)

# Log end of experiment
logging.log(level=logging.EXP, msg='--- END EXPERIMENT ---')

# exit experiment
CoolDown()

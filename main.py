from cmu_112_graphics import *
import numpy as np
import math
import random

#####################################################################  
# Classes  
#####################################################################
# A class that represent all 3D objects
class threeDimensionObject(object):
    # Initialization of parameters
    def __init__(self,x,y,z):
        self.x = x
        self.y = y
        self.z = z

    # return a matrix that is the coordinate of the ball in 3D (x,y,z)
    def get3DCoor(self):
        return np.array([[self.x],[self.y],[self.z]])

    # return three values. First two are x and y coordinates after projected
    # into 2D frame. The third value is the zoomed radius of the ball
    def get2DCoor(self):
        projectionMatrix = np.array([[1,0,0],
                                     [0,1,0]])
        rotationMatrix = self.matrixConvertConstant()
        ballPos = np.array([[self.x],[self.y],[self.z]])
        rotated = np.dot(rotationMatrix,ballPos)
        rotated = np.dot(projectionMatrix,rotated)
        x = self.originX + int(rotated[0][0])
        y = self.originY + int(rotated[1][0])
        r = self.r - int(ballPos[2][0]) / self.ballZoomScale
        return x,y,r

    # Set up the 3D coordinate system, so that any matrix of (x,y,z) can 
    # mulitply this constant (dot product) and then multiply the projection 
    # matrix to get a 2D coordinate (x,y)
    def matrixConvertConstant(self):
        pi = np.pi
        angleX = pi * 135 / 180
        angleY = pi * 2 / 180
        angleZ = pi * 0 / 180
        # rotation according to x-axis (formula from wikipedia)
        rotationX = np.array([[1 , 0              , 0              ],
                              [0 , np.cos(angleX) , -np.sin(angleX)],
                              [0 , np.sin(angleX) , np.cos(angleX)]])
        # rotation according to y-axis (formula from wikipedia)
        rotationY = np.array([[np.cos(angleY) , 0 , np.sin(angleY)],
                              [0              , 1 , 0             ],
                              [-np.sin(angleY), 0 , np.cos(angleY)]])
        # rotation according to z-axis (formula from wikipedia)
        rotationZ = np.array([[np.cos(angleZ) , -np.sin(angleZ), 0             ],
                              [np.sin(angleZ) , 0              , np.cos(angleZ)],
                              [0              , 0              , 1             ]])
        result = np.dot(rotationX,rotationY)
        return result


# creating an object class to control the ball (Inhertence from 3DObject)
class Ball(threeDimensionObject):
    # Initialization of parameters
    def __init__(self,x,y,z):
        super().__init__(x,y,z)
        self.originX = 347
        self.originY = 350
        self.vX = 0
        self.vY = 20
        self.vZ = 0
        self.accX = 0
        self.accY = -3
        self.accZ = 0
        self.airResistance = 0.6
        self.r = 10
        self.ballZoomScale = 40
        self.moving = False
        self.touched = False
        self.touchedTime = 0

    
# creating an object to represent opponent's bat (Inhertence from 3DObject)
class opponentBat(threeDimensionObject):
    def __init__(self,x,y,z):
        super().__init__(x,y,z)
        self.originX = 347
        self.originY = 350
        self.zoomScale = 60
    
    # Override the function in 3D object class
    def get2DCoor(self):
        projectionMatrix = np.array([[1,0,0],
                                     [0,1,0]])
        rotationMatrix = self.matrixConvertConstant()
        ballPos = np.array([[self.x],[self.y],[self.z]])
        rotated = np.dot(rotationMatrix,ballPos)
        rotated = np.dot(projectionMatrix,rotated)
        x = self.originX + int(rotated[0][0])
        y = self.originY + int(rotated[1][0])
        return x,y,1


# creating an object  to control bat
class Bat(object):
    # Initialization of parameters
    def __init__(self,app):
        self.lenTracked = 4
        self.prevX = [0] * self.lenTracked # list of previous few position
        self.prevY = [0] * self.lenTracked
        self.x = 1/2 * app.width
        self.y = 3/4 * app.height
        self.dx = 0
        self.dy = 0
        self.v = 0
    
    # Calculate the velocity of the bat
    def findVelocity(self):
        length = len(self.prevX) - 1
        countX = 0
        countY = 0
        for i in range (length):
            countX += (self.x - self.prevX[i])
            countY += (self.y - self.prevY[i])
        if length != 0:
            self.dx = countX / (length)
            self.dy = countY / (length)
            self.v = (self.dx ** 2 + self.dy ** 2) ** 0.5

    # rotate myBat based on the position of the mouse
    def rotateBat(self,app):
        newX = self.x
        middleX = app.width/2
        if newX < middleX:
            app.rotatedMyBat = app.imageMyBat.rotate(-(newX-middleX) / middleX * 90)
        else:
            app.rotatedMyBat = app.imageMyBat.rotate((middleX-newX) / middleX * 90)


#####################################################################  
# Ball Motion 
#####################################################################
# movement of the ball
def move(app,ball,bat):
    if ball.moving and app.gameState:
        if isHitted(app,ball,bat):
            app.calculated = False
            app.oppoHitted = False
            app.roundStart = True
            ball.touched = True
            ball.touchedTime = 0
            app.turn = "oppo"
            ball.vX = (bat.prevX[-1] - bat.prevX[0]) / 20
            if bat.v != 0:
                # calculate force of hitting the ball
                ball.vY = abs(ball.vY) + 11 + 5 / (1 + math.e ** (0.05*(ball.y-100)))
                ball.vZ = 8 + 1 / (1 + math.e ** (-0.05 * (bat.v - 100)))
            else:
                # if the bat is not moving (player not move mouse)
                ball.vY = abs(ball.vY)
                ball.vZ = 6
            # check rotation
            if app.rotationMode == True:
                ball.accX = - bat.dx / 150
        verticalMove(ball)
        forwardMove(ball)
        horizontalMove(ball)

# consider the gravity and air resistance's impact on ball's vertical move
def verticalMove(ball):
    # free fall due to gravity
    ball.vY += ball.accY
    if ball.vY > 0:
        ball.vY -= ball.airResistance
    else:
        ball.vY += ball.airResistance
    ball.y += ball.vY
    # if touch table, then rebound (error becomes energy lose)
    if ball.y <= 0:
        ball.y = 0
        ball.vY = abs(ball.vY)
        ball.touchedTime += 1

# check if the ball is hit by the bat
def isHitted(app,ball,bat):
    # make sure only hit the ball once and not touch the ball before it 
    # pass the net
    batMargin = 45
    if ball.touched or ball.z > app.netZ:
        return False
    # any point on the line is considered to be hitted (so not miss any point)
    elif (app.ballY > ((bat.prevY[-1]+bat.prevY[0])/2 - batMargin) and
         ((app.ballX >= (bat.prevX[0] - batMargin) and app.ballX <= (bat.prevX[-1] + batMargin)) or
          (app.ballX >= (bat.prevX[-1] - batMargin) and app.ballX <= (bat.prevX[0] + batMargin)))):
        return True
    else:
        return False

# horizontal move
def forwardMove(ball):
    ball.z += ball.vZ

# move along x-axis (consider rotation)
def horizontalMove(ball):
    ball.vX += ball.accX
    ball.x += ball.vX


#####################################################################  
# Rules Check  
#####################################################################

# check if the game is ended
def checkEndGame(app):
    checkTouchNet(app)
    checkBounce(app)
    checkOutOfTable(app)

# check if the ball touch the net
def checkTouchNet(app):
    netHeight = 30
    #check the height of the ball compared with the net
    if (app.netZ - app.ball.vZ <= app.ball.z <= app.netZ + app.ball.vZ):
        if app.ball.y < netHeight:
            if app.turn == "oppo" and app.ball.moving:
                app.oppoScore += 1
                app.endReason = ("The Ball Touches The Net!\n\t" + 
                                 "You lose this round")
            elif app.turn == "me" and app.ball.moving:
                app.myScore += 1
                app.endReason = ("The Ball Touches The Net!\n\t" + 
                                 "A.I. loses this round")
            app.isEnded = True
            app.ball.moving = False
            app.roundStart = False

# check if the ball bounce twice on the same side
def checkBounce(app):
    if (app.turn == "oppo" and app.ball.moving and 
        app.ball.z < app.netZ and app.ball.touchedTime > 0):
            app.oppoScore += 1
            app.endReason = ("The Ball Touches Your Side Twice!\n\t" + 
                             "You lose this round")
            app.isEnded = True
            app.ball.moving = False
            app.roundStart = False
    elif (app.turn == "me" and app.ball.moving and 
          app.netZ < app.ball.z < 235 and app.ball.touchedTime > 0):
            app.myScore += 1
            app.endReason = ("The Ball Touches A.I.'s Side Twice!\n\t" + 
                             "A.I. loses this round")
            app.isEnded = True
            app.ball.moving = False
            app.roundStart = False
        
# check if the ball flies out of the table without bouncing
def checkOutOfTable(app):
    if app.ball.y <= 0 and app.ball.moving and checkOutOfTableConditionHelper(app):
        if ((app.turn == "oppo" and app.ball.touchedTime == 1) or
            (app.turn == "me" and app.ball.touchedTime > 1)):
            app.oppoScore += 1
            app.endReason = ("You Don't Hit The Table!\n" +
                             "You lose this round")
        elif ((app.turn == "me" and app.ball.touchedTime == 1) or 
              (app.turn == "oppo" and app.ball.touchedTime > 1)):
            app.myScore += 1
            app.endReason = ("A.I. Don't Hit The Table!\n" +
                             "A.I. loses this round")
        app.isEnded = True
        app.ball.moving = False
        app.roundStart = False
        
# check both x-axis and z axis to see if the ball is out of table
def checkOutOfTableConditionHelper(app):
    # this number is calculated by linear regression (since table is a 3D object)
    xBound = -0.469 * app.ball.z + 260
    if app.ball.x < -1*xBound or app.ball.x > xBound:
        return True
    elif app.ball.z < 0 or app.ball.z > 240:
        return True
    else:
        return False

# check if either side reaches 11 points or higher when both in match point
def checkReach11(app):
    winScore = 11
    if app.myScore >= winScore:
        if app.oppoScore < app.myScore - 1:
            app.winner = "You"
            app.gameState = False
            clearMemory()
    elif app.oppoScore >= winScore:
        if app.myScore < app.oppoScore - 1:
            app.winner = "A.I."
            app.gameState = False
            clearMemory()

# clear the game data when one side reach 11 (add this part for bug)
def clearMemory():
    dataPath = "data/game data.txt"
    file = open(dataPath,"w")
    file.write("")
    file.close()

#####################################################################  
# Game AI  
#####################################################################
# let AI serve the ball
def AIHitMove(app,ball,oppoBat):
    xSpeed = 5
    if oppoBat.x < ball.x:
        oppoBat.x += xSpeed
    # hit the ball after it bounce one time
    if ball.touchedTime > 0:
        oppoBat.y += 10
        oppoBat.z -= 5
    # hit the ball
    if checkOppoHit(app,ball,oppoBat) and not app.oppoHitted:
        app.oppoHitted = True
        serveTheBall(app,ball)
        app.AIHit = False
        app.roundStart = True

# hit the ball when serving
def serveTheBall(app,ball):
    ball.vZ = -8
    ball.vY = 30
    ball.vX = random.randint(-16,6)
    ball.touched = False
    ball.touchedTime = 0
    app.turn = "me"

# move the opponent's bat (easy mode)
def AIOpponentMoveEasy(app,ball,oppoBat):
    if ball.moving:
        if checkOppoHit(app,ball,oppoBat) and not app.oppoHitted:
            app.oppoHitted = True
            hitTheBall(app,ball)
        batHorizontalMotion(app,ball,oppoBat)
        if ball.z > app.netZ:
            batVerticalMotionEasy(ball,oppoBat)
            batForwardMotionEasy(app,ball,oppoBat)

# vertical motion of AI (easy mode)
def batVerticalMotionEasy(ball,oppoBat):
    oppoBatVY = 5
    if ball.touchedTime > 0:
        if oppoBat.y < ball.y:
            oppoBat.y += oppoBatVY
        elif oppoBat.y > ball.y:
            oppoBat.y -= oppoBatVY

# forward motion of AI (easy mode)
def batForwardMotionEasy(app,ball,oppoBat):
    originZ = 235
    oppoBatVZ = 5
    error = 4
    distance = 30
    minZ = 160 # bat will stop at this position and not move forward
    maxZ = 235 # bat will stop at this position and not move backward
    # go back to origin when in my turn
    if app.turn == "me" :
        if oppoBat.z < originZ:
            oppoBat.z += oppoBatVZ
        elif oppoBat.z > originZ:
            oppoBat.z -= oppoBatVZ
    # track the ball's forward motion in opponent's turn
    elif app.turn == "oppo" and ball.touchedTime > 0:
        if oppoBat.z < ball.z - error:
            oppoBat.z += oppoBatVZ
        elif oppoBat.z > ball.z + error:
            oppoBat.z -= oppoBatVZ
    elif app.turn == "oppo" and ball.touchedTime == 0:
        if oppoBat.z - ball.z > distance and oppoBat.z > minZ:
            oppoBat.z -= ball.vZ
        elif oppoBat.z - ball.z < distance and oppoBat.z < maxZ:
            oppoBat.z += ball.vZ

# move the opponent's bat (hard mode)
def AIOpponentMoveAdvanced(app,ball,oppoBat):
    if ball.moving:
        if ball.z > app.netZ and ball.y >= app.netY and not app.calculated:
            app.calculated = True
            app.targetY,app.targetZ = calculateCoor(app,ball)
        batHorizontalMotion(app,ball,oppoBat)
        batForwardMotion(app,ball,oppoBat)
        batVerticalMotion(app,ball,oppoBat)
        if checkOppoHit(app,ball,oppoBat) and not app.oppoHitted:
            app.oppoHitted = True
            hitTheBall(app,ball)

# calculate the y and z coordinate for opponent's bat to hit the ball
def calculateCoor(app,ball):
    hitPlace = 0.5
    # Derive to formula x = x0 + v0x*t + 0.5*a*t^2, we can calculate the 
    # delta T for the ball to land on the table
    vY0 = ball.vY
    h0 = ball.y
    g = ball.accY + ball.airResistance
    t = max((-vY0 - (vY0**2 - 2*g*h0)**0.5) / g, (-vY0 + (vY0**2 - 2*g*h0)**0.5) / g)
    # calculate the z coordinate to hit the ball using x = v*t
    vZ0 = ball.vZ
    hitZ = (1+hitPlace) * vZ0 * t + app.netZ
    # First need to calculate the upward velocity Y after bouncing
    # Uses formula Vf = Vi + a*t, also assume no energy lose during collision
    vUpward = -(vY0 + g * t)
    # Ualculate the height of the bat to hit the ball at hitZ
    # Use formula x = x0 + v0x*t + 0.5*a*t^2 again to find final height
    g = ball.accY - ball.airResistance
    hFinal = 0 + vUpward * hitPlace * t + 0.5 * g * (hitPlace * t) **2
    return hFinal, hitZ

# track the ball's horizaontal motion, let the opponent's bat react correspondingly
def batHorizontalMotion(app,ball,oppoBat):
    oppoBatVX = 10
    r = app.oppoBatRange
    if ball.touched:
        if ball.x > (oppoBat.x+r):
            oppoBat.x += oppoBatVX
        elif ball.x  < (oppoBat.x-r):
            oppoBat.x -= oppoBatVX
    else:
        if oppoBat.x > 0:
            oppoBat.x -= oppoBatVX
        elif oppoBat.x < 0:
            oppoBat.x += oppoBatVX

# move the bat forward to hit the ball
def batForwardMotion(app,ball,oppoBat):
    originZ = 235
    oppoBatVZ = 5
    error = 4
    # go back to origin when in my turn
    if app.turn == "me" :
        if oppoBat.z < originZ:
            oppoBat.z += oppoBatVZ
        elif oppoBat.z > originZ:
            oppoBat.z -= oppoBatVZ
    # track the ball's forward motion in opponent's turn
    elif app.turn == "oppo" and ball.z > app.netZ:
        if (isinstance(app.targetZ,float) and 
            oppoBat.z < app.targetZ - error):
            oppoBat.z += oppoBatVZ
        elif (isinstance(app.targetZ,float) and 
                oppoBat.z > app.targetZ + error):
            oppoBat.z -= oppoBatVZ

# move the bat up to hit the ball
def batVerticalMotion(app,ball,oppoBat):
    originY = 50
    oppoBatVY = 5
    error = 4
    # go back to origin when in my turn
    if app.turn == "me" :
        if oppoBat.y < originY:
            oppoBat.y += oppoBatVY
        elif oppoBat.y > originY:
            oppoBat.y -= oppoBatVY
    # track the ball's forward motion in opponent's turn
    elif app.turn == "oppo" and ball.z > app.netZ:
        if (isinstance(app.targetY,float) and 
            oppoBat.y < app.targetY - error):
            oppoBat.y += oppoBatVY
        elif (isinstance(app.targetY,float) and 
                oppoBat.y > app.targetY + error):
            oppoBat.y -= oppoBatVY

# check if the opponent's bat hit the ball
def checkOppoHit(app,ball,oppoBat):
    batThick = 10
    r = app.oppoBatRange
    if ball.z - batThick <= oppoBat.z <= ball.z + batThick:
        if ((ball.x - r <= oppoBat.x <= ball.x + r) and
            (ball.y - r <= oppoBat.y <= ball.y + r)):
            return True
    return False

# let AI's bat hit the ball
def hitTheBall(app,ball):
    error = 5
    ball.vZ *= -1
    ball.vY,targetZ = getVY(ball)
    ball.vY -= error
    ball.vX = getVX(ball,targetZ)
    ball.accX = 0
    ball.touched = False
    ball.touchedTime = 0
    app.turn = "me"

# use physical simulation to get velocity to hit the ball by A.I.
def getVY(ball):
    vZ = ball.vZ
    accUp = ball.accY - ball.airResistance
    accDown = ball.accY + ball.airResistance
    zIni = ball.z
    hIni = ball.y
    targetZ = random.randint(50,90)
    ZTravel = zIni - targetZ
    # ##### This is the physical proof #####
    #
    # Because the time travel in y direction is the same as the time travel 
    # in z direction, so I can have the equation: Ty,up + Ty,down = Tz.
    # Using the formula Vx = V0 + ax * t, Ty,up = -Vy / aUp
    # To find Ty,down, we first need to find maximum height that ball can reach
    # Using formula x = x0 + v0*t + 0.5*a*t^2, we can know that
    # max height is h - (vy)^2 / (2*aUp)
    # Again use the formula x = x0 + v0*t + 0.5*a*t^2, we can find that
    # Ty,down = ((vY^2/aUp - 2*h) / aDown)^0.5
    # Using formula t = x / v, we can know that Tz = Xz / Vz
    # Equation becomes -Vy / aUp + ((vY^2/aUp - 2*h) / aDown)^0.5 = Xz / Vz
    # solve for Vy, we can get a quadratic equation with one unknown:
    # (aUp-aDown)*Vy^2 + 2*x*aUp*aDown/vX * vY + aUp^2*aDown*(2h/aDown-x^2/vX^2) = 0
    # list a,b,c of this quadratic equation (ax^2+bx+c = 0)
    a = accUp - accDown
    b = 2*ZTravel*accUp*accDown/vZ
    c = accUp**2*accDown*(2*hIni/accDown-(ZTravel/vZ)**2)
    # using formula to solve the root
    vY = max((-b+(b**2-4*a*c)**0.5)/(2*a),(-b-(b**2-4*a*c)**0.5)/(2*a))
    return vY, ZTravel/vZ

# return the force that A.I. hit the ball
def getVX(ball,target):
    XMax = 240
    XMin = -240
    time = (ball.z - target) / - ball.vZ
    VXMax = (XMax - ball.x) / time
    VXMin = (XMin - ball.x) / time
    return random.uniform(VXMin,VXMax)

#####################################################################  
# Help Mode Mode
#####################################################################
# draw the screen
def helpMode_redrawAll(app, canvas):
    # display based on page number
    if app.helpPage == 0:
        canvas.create_text(350,75, text = "How To Play The Game", 
                           fill = "blue", font = "Times 35 bold italic")
        canvas.create_text(100,400,text = "1. Move your mouse to control the"+
                            " bat\n\n2. When its your turn to serve the ball"+
                            ",\nright click you mouse to throw the ball\n\n3"+
                            ". Try to hit the ball onto the table, pass\nthe"+
                            " net, and not rebound twice\n\n4. First play wh"+
                            "o reach 11 points win\nthe game\n\n\nAdvanced: "+
                            "Press Enter to switch to the\nrotation mode",
                           anchor = "w", font = "Times 24 bold italic")
    elif app.helpPage == 1:
        canvas.create_image(app.width/2, app.height/2, 
                            image=ImageTk.PhotoImage(app.storyBoard))
    # create buttons
    canvas.create_rectangle(620,660,697,697, fill = "yellow", width = 2)
    canvas.create_text(660,680, text = "Next", fill = "black",
                       font = "Times 12 bold italic")
    canvas.create_rectangle(620,3,697,40, fill = "yellow", width = 2)
    canvas.create_text(660,20, text = "Back", fill = "black",
                       font = "Times 12 bold italic")

# when click either button, mode changes
def helpMode_mousePressed(app,event):
    if 620 <= event.x <= 700 and 0 <= event.y <= 40:
        app.helpPage = 0
        app.mode = "splashScreen"
    elif 620 <= event.x <= 700 and 640 <= event.y <= 700:
        app.helpPage = 1 - app.helpPage


#####################################################################  
# Splash Screen Mode
#####################################################################
# draw the screen
def splashScreen_redrawAll(app, canvas):
    canvas.create_image(app.width/2 + 10, app.height/2, 
                        image=ImageTk.PhotoImage(app.startImage))
    canvas.create_text(320,150, text = "112 Ping-Pong", fill = "yellow",
                       font = "Times 60 bold italic")
    canvas.create_rectangle(620,3,697,40, fill = "yellow", width = 2)
    canvas.create_text(660,20, text = "Help", fill = "black",
                       font = "Times 12 bold italic")
    canvas.create_rectangle(80,320,280,380, fill = "blue", width = 2)
    canvas.create_text(180,350, text = "New Game", fill = "black",
                       font = "Times 24 bold italic")
    if app.myScore != 0 or app.oppoScore != 0:
        canvas.create_rectangle(80,420,280,480, fill = "blue", width = 2)
        canvas.create_text(180,450, text = "Resume", fill = "black",
                           font = "Times 24 bold italic")
    if app.chooseLevel:
        canvas.create_rectangle(200,200,500,500, fill = "blue")
        # back button
        canvas.create_rectangle(480,200,500,220, fill = "yellow")
        canvas.create_line(482,202,498,218, fill = "black", width = 3)
        canvas.create_line(482,218,498,202, fill = "black", width = 3)
        # easy mode
        canvas.create_rectangle(250,250,450,325, fill = "yellow")
        canvas.create_text(350,287.5, text = "Easy", fill = "black",
                           font = "Times 24 bold italic")
        # hard mode
        canvas.create_rectangle(250,375,450,450, fill = "yellow")
        canvas.create_text(350,412.5, text = "Hard", fill = "black",
                           font = "Times 24 bold italic")

# when click either button, mode changes
def splashScreen_mousePressed(app,event):
    mouseX = event.x
    mouseY = event.y
    # click "help" button
    if 620 <= mouseX <= 700 and 0 <= mouseY <= 40:
        app.chooseLevel = False
        app.mode = "helpMode"
    # click "new game" button
    elif 80 <= mouseX <= 280 and 320 <= mouseY <= 380 and not app.chooseLevel:
        app.chooseLevel = True
    # click X to go back
    elif app.chooseLevel and 480 <= mouseX <= 500 and 200 <= mouseY <= 220:
        app.chooseLevel = False
    # choose easy level
    elif app.chooseLevel and 250 <= mouseX <= 450 and 250 <= mouseY <= 325:
        app.chooseLevel = False
        app.level = 0
        startGame(app)
    # choose hard level
    elif app.chooseLevel and 250 <= mouseX <= 450 and 375 <= mouseY <= 450:
        app.chooseLevel = False
        app.level = 1
        startGame(app)
    # click "resume" buttons
    elif ((app.myScore != 0 or app.oppoScore != 0) and 
          80 <= mouseX <= 280 and 420 <= mouseY <= 480):
        loadMemory(app)
        placeBall(app)
        app.chooseLevel = False
        app.mode = "gameMode"

# set parameters that start the game
def startGame(app):
    app.myScore = 0
    app.oppoScore = 0
    app.myScoreboardX = 80
    app.oppoScoreboardX = 80
    app.gameState = True
    app.roundStart = False
    app.winner = None
    app.serving = "me"
    app.servingCount = 0
    restartGame(app)
    updateMemory(app)
    app.mode = "gameMode"

#####################################################################  
# Game Mode  
#####################################################################
# every time move the ball and update the coor of ball
def gameMode_timerFired(app):
    if app.gameState:
        app.myBat.findVelocity()
        app.myBat.rotateBat(app)
        move(app,app.ball,app.myBat)
        updateBatCoor(app)
        updateBallCoor(app)
        batZoom(app)
        serveOrHit(app)
        checkEndGame(app)
        scoreboardAnimation(app)
        timeAccumulate(app)

# add time to time counter, restart the game after certain amont of time
def timeAccumulate(app):
    app.timerDelay = 5
    timeWait = 250
    if not app.checkedEnd and app.isEnded:
        updateMemory(app)
        checkReach11(app)
        app.checkedEnd = True
    if app.gameState and app.timeCounter > timeWait:
        restartGame(app)
        app.checkedEnd = False
    elif app.gameState and app.isEnded:
        app.timeCounter += app.timerDelay

# determine currenting is hitting the ball or serving the ball, 
# choose corresponding algorithm
def serveOrHit(app):
    if app.AIHit == True:
        app.ball.moving = True
        AIHitMove(app,app.ball,app.oppoBat)
    elif app.level == 0:
        AIOpponentMoveEasy(app,app.ball,app.oppoBat)
    else:
        AIOpponentMoveAdvanced(app,app.ball,app.oppoBat)
    
# move the scoreboard to show to lead
def scoreboardAnimation(app):
    minX = 80
    maxX = 110
    moveSpeed = 2
    if app.myScore == app.oppoScore:
        if app.myScoreboardX > minX:
            app.myScoreboardX -= moveSpeed
        if app.oppoScoreboardX > minX:
            app.oppoScoreboardX -= moveSpeed
    elif app.myScore > app.oppoScore:
        if app.myScoreboardX < maxX:
            app.myScoreboardX += moveSpeed
        if app.oppoScoreboardX > minX:
            app.oppoScoreboardX -= moveSpeed
    elif app.myScore < app.oppoScore:
        if app.myScoreboardX > minX:
            app.myScoreboardX -= moveSpeed
        if app.oppoScoreboardX < maxX:
            app.oppoScoreboardX += moveSpeed

# make the opponent's bat big and small based on its coordinate
def batZoom(app):
    app.imageOppoBat = app.scaleImage(app.imageBat,1/8 * (235/app.oppoBat.z))
    if app.oppoBat.x >= 0:
        app.imageOppoBat = app.imageOppoBat.rotate(-135)
    else:
        app.imageOppoBat = app.imageOppoBat.rotate(135)

# update the txt file after each round
def updateMemory(app):
    dataPath = "data/game data.txt"
    file = open(dataPath,"w")
    file.write(f"{app.myScore} {app.oppoScore} {app.serving} {app.servingCount} {app.level}")
    file.close()

# When each round start, press mouse to shoot the ball
def gameMode_mousePressed(app,event):
    if 620 <= event.x <= 700 and 0 <= event.y <= 40:
        app.mode = "splashScreen"
    elif not app.ball.moving and not app.isEnded:
        app.ball.moving = True

# key "a" and "d" control x axis movement of the ball
# key "w" and "s" control y axis movement of the ball (vertical)
# key "q" and "e" control z axis movement of the ball
# when press "Space", the ball start moving, press again, stop moving
def gameMode_keyPressed(app, event):
    if event.key == "a":
        app.myScore += 1
    elif event.key == "d":
        app.oppoScore += 1
    elif event.key == "r":
        restartGame(app)
    elif event.key == "p":
        if app.roundStart:
            app.ball.moving = not app.ball.moving
    elif event.key == "Enter":
        app.rotationMode = not app.rotationMode

# keep track of the place of the mouse, which is the position of the bat
def gameMode_mouseMoved(app,event):
    app.myBat.x = event.x
    app.myBat.y = event.y
    updateBatCoor(app)

# draw the pingpong ball
def drawBall(app, canvas):
    x,y,r = app.ballX,app.ballY,app.r
    canvas.create_oval(x-r, y-r, x+r, y+r, fill = "red")

# draw the pingpong bat
def drawBats(app,canvas):
    canvas.create_image(app.myBat.x, app.myBat.y, 
                        image=ImageTk.PhotoImage(app.rotatedMyBat))
    canvas.create_image(app.oppoBatX, app.oppoBatY, 
                        image=ImageTk.PhotoImage(app.imageOppoBat))

# show player the mode they are current in
def drawMode(app,canvas):
    canvas.create_rectangle(150,650,550,700,fill = "blue")
    canvas.create_text(200,675,text = "Mode: ", font = "Times 20 bold italic")
    canvas.create_text(290,675,text = "Normal", font = "Times 20 bold italic")
    canvas.create_text(460,675,text = "Rotation", font = "Times 20 bold italic")
    if app.rotationMode == False:
        canvas.create_oval(340,685,360,665,fill = "yellow")
    else:
        canvas.create_oval(520,685,540,665,fill = "yellow")

# displace on the screen the reason why the game ends
def showEndReason(app,canvas):
    if app.isEnded:
        canvas.create_text(0.5 * app.width, 120, text = app.endReason, 
                           fill = "yellow", font = "Times 30 bold italic")

# draw the scoreboard and write scores
def drawScoreBoard(app,canvas):
    # draw the base board
    canvas.create_image(app.myScoreboardX,40,image=ImageTk.PhotoImage(app.imageMyScoreboard))
    canvas.create_image(app.oppoScoreboardX,90,image=ImageTk.PhotoImage(app.imageOppoScoreboard))
    # create text
    canvas.create_text(app.myScoreboardX,43,text = f"Me:     {app.myScore}",
                       font="Times 15 bold italic")
    canvas.create_text(app.oppoScoreboardX,93,text = f"A.I:    {app.oppoScore}",
                       font="Times 15 bold italic")

# write winner when the whole game ends(when someone reaches 11)
def declearWinner(app,canvas):
    if app.gameState == False:
        canvas.create_rectangle(150,300,550,400, fill = "blue")
        canvas.create_text(app.width/2,app.height/2,
                           text = f"{app.winner} win the game\nClick Menu to restart",
                           fill = "black", font = "Times 30 bold italic")

# draw the table, floor, and other background
def drawBackground(app,canvas):
    # draw floor
    #canvas.create_image(app.width/2, app.height/2, 
    #                    image=ImageTk.PhotoImage(app.imageFloor))
    # draw table
    canvas.create_image(app.width/2, app.height/2, 
                        image=ImageTk.PhotoImage(app.imageTable))

# draw the menu button onto canvas
def drawButton(app,canvas):
    canvas.create_rectangle(620,3,697,40, fill = "gray", width = 2)
    canvas.create_text(660,20, text = "Menu", fill = "black",
                       font = "Times 12 bold italic")

# draw a circle that represent pause when the player press "P"
def drawPause(app,canvas):
    if app.roundStart and not app.ball.moving:
        canvas.create_oval(250,250,450,450, fill = "blue", width = 3)
        canvas.create_polygon(315,300,415,350,315,400, fill = "gray")

# draw all the things
def gameMode_redrawAll(app, canvas):
    drawBackground(app,canvas)
    drawButton(app,canvas)
    drawScoreBoard(app,canvas)
    drawMode(app,canvas)
    drawBats(app,canvas)
    drawBall(app,canvas)
    drawPause(app,canvas)
    showEndReason(app,canvas)
    declearWinner(app,canvas)


#####################################################################
# Main
#####################################################################
# initialize parameters
def appStarted(app):
    loadImage(app)
    loadMemory(app)
    app.mode = "splashScreen"
    app.targetY = None
    app.targetZ = None
    app.netZ = 145
    app.netY = 50
    app.oppoBatRange = 25
    app.gameState = True  # means that the game is not end (reach 11 pts)
    app.winner = None
    app.rotationMode = False
    app.serving = "me"
    app.servingCount = 0
    app.AIHit = False
    app.myScoreboardX = 80
    app.oppoScoreboardX = 80
    app.roundStart = False
    app.helpPage = 0
    app.level = -1
    app.chooseLevel = False
    app.checkedEnd = False
    restartGame(app)

# load all images
def loadImage(app):
    ImagePath = "game images/"
    app.storyBoard = app.loadImage('storyboard.jpg')
    app.storyBoard = app.scaleImage(app.storyBoard,1/2)
    # citation: image from https://www.advancedsciencenews.com/the-future-of-athletics-smart-ping-pong-paddles/
    app.startImage = app.loadImage(ImagePath + 'start_image.png')
    app.startImage = app.scaleImage(app.startImage,1.2)
    # citation: image from https://thefloorstorenm.com/
    # citation: image from https://unsplash.com/s/photos/wall
    # citation: image from https://www.wanwupai.com/rank/6432.html
    # photoshoped and get the "background.jpg"
    app.imageTable = app.loadImage(ImagePath + 'background.jpg')
    # citation: image from https://toppng.com/free-download-vector-box-design-PNG-free-PNG-Images_193382
    # photoshoped to make it transparent
    app.imageScoreboard = app.loadImage(ImagePath + 'scorebox.png')
    app.imageMyScoreboard = app.scaleImage(app.imageScoreboard,1/5)
    app.imageOppoScoreboard = app.scaleImage(app.imageScoreboard,1/5)
    # citation: image from https://www.winmaxsport.com/rubber-table-tennis-racket-ping-pong-paddle-wooden-rubber-table-tennis-bat.html
    app.imageBat = app.loadImage(ImagePath + 'ping_pong_bat.png')
    app.imageMyBat = app.scaleImage(app.imageBat,1/4)
    app.rotatedMyBat = app.imageMyBat.rotate(0)
    app.imageOppoBat = app.scaleImage(app.imageBat,1/8)
    app.imageOppoBat = app.imageOppoBat.rotate(-135)

# load os file to read old score
def loadMemory(app):
    dataPath = "data/game data.txt"
    file = open(dataPath,"r")
    data = file.read()
    if data == "":
        app.myScore = 0
        app.oppoScore = 0
        app.serving = "me"
        app.servingCount = 0
        app.level = -1
    else:
        dataList = data.split(" ")
        app.myScore = int(dataList[0])
        app.oppoScore = int(dataList[1])
        app.serving = dataList[2]
        app.servingCount = int(dataList[3])
        app.level = int(dataList[4])
    file.close()

# place the ball based on server
def placeBall(app):
    if app.serving == "me":
        app.ball = Ball(-100,200,20)
        app.turn = "me"
    else:
        app.ball = Ball(100,200,220)
        app.AIHit = True
        app.turn = "oppo"

# reset all the parameters
def restartGame(app):
    changeServe(app)
    placeBall(app)
    app.oppoBat = opponentBat(0,50,235)
    app.myBat = Bat(app)
    app.isEnded = False
    app.endReason = ""
    app.timeCounter = 0
    app.oppoHitted = False
    app.calculated = False
    updateBallCoor(app)

# change server every 2 round
def changeServe(app):
    app.servingCount += 1
    if app.servingCount == 3:
        app.servingCount = 1
        if app.serving == "me":
            app.serving = "oppo"
        else:
            app.serving = "me"

# update the real time x,y,r to the app
def updateBallCoor(app):
    app.ballX,app.ballY,app.r = app.ball.get2DCoor()
    app.oppoBatX, app.oppoBatY, app.oppoBatR = app.oppoBat.get2DCoor()

# update the real time bat coordinate
def updateBatCoor(app):
    app.myBat.prevX.append(app.myBat.x)
    app.myBat.prevY.append(app.myBat.y)
    if len(app.myBat.prevX) > app.myBat.lenTracked:
        app.myBat.prevX.pop(0)
        app.myBat.prevY.pop(0)


# run the game
def main():
    print('Run the Game!')
    runApp(width=700, height=700)

main()

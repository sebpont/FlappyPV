# -*- coding: utf-8 -*-
"""
Created on Thu Apr 20 15:26:12 2017

@author: sp4009
"""
import serial
import math
import os
import datetime
import operator
import pygame
from random import randint
from pygame.locals import *

FPS = 60					 # frames per second
FRAME_ANIMATION_WIDTH = 8      # pipe pixels move per frame
EVENT_NEWPIPE = USEREVENT + 1  # custom event

WIN_WIDTH = 1580   # screen size, pixels
WIN_HEIGHT = 950

PIPE_WIDTH = 150
PIPE_PIECE_HEIGHT = 32
BIRD_HEIGHT = 80 # same as cat and dog hieght
BIRD_WIDTH = 148
CAT_WIDTH = 175
DOG_WIDTH = 94

"""
This version is played with 3 solar cells: (code could be developed to dictionaries to easily change the number of players)
silicon - 'bird'
cat - 'OPV'
dog - 'perovskite'
"""

BIRD_MaxV = 3 * (1023 / 5) #voltage converted to 1024-byte chunks (0-1023) that arduino gives
BIRD_MinV = 5 * (1023 / 5)
CAT_MaxV = 0 * (1023 / 5)
CAT_MinV = 0.24 * (1023 / 5)
DOG_MaxV = 0 * (1023 / 5)
DOG_MinV = 3.5 * (1023 / 5)

bird_score = 0
cat_score = 0
dog_score = 0

arduino_port = '/dev/ttyACM0'
    
class PipePair:
    """Represents an obstacle.

    A PipePair has a top and a bottom pipe, and only between them can
    the bird pass -- if it collides with either part, the game is over.

    Attributes:
    x: The PipePair's X position.  Note that there is no y attribute,
        as it will only ever be 0.
    surface: A pygame.Surface which can be blitted to the main surface
        to display the PipePair.
    top_pieces: The number of pieces, including the end piece, in the
        top pipe.
    bottom_pieces: The number of pieces, including the end piece, in
        the bottom pipe.
    """

    def __init__(self, surface, top_pieces, bottom_pieces):
        """Initialises a new PipePair with the given arguments.

        The new PipePair will automatically be assigned an x attribute of
        WIN_WIDTH.

        Arguments:
        surface: A pygame.Surface which can be blitted to the main
            surface to display the PipePair.  You are responsible for
            converting it, if desired.
        top_pieces: The number of pieces, including the end piece, which
            make up the top pipe.
        bottom_pieces: The number of pieces, including the end piece,
            which make up the bottom pipe.
        """
        self.x = WIN_WIDTH
        self.surface = surface
        self.top_pieces = top_pieces
        self.bottom_pieces = bottom_pieces
        self.bird_score_counted = False
        self.cat_score_counted = False
        self.dog_score_counted = False
        
    @property
    def top_height_px(self):
        """Get the top pipe's height, in pixels."""
        return self.top_pieces * PIPE_PIECE_HEIGHT

    @property
    def bottom_height_px(self):
        """Get the bottom pipe's height, in pixels."""
        return self.bottom_pieces * PIPE_PIECE_HEIGHT

    def is_bird_collision(self, bird_position):
        """Get whether the bird crashed into a pipe in this PipePair.

        Arguments:
        bird_position: The bird's position on screen, as a tuple in
            the form (X, Y).
        """
        bx, by = bird_position
        in_x_range = bx - 0.5 * PIPE_WIDTH < self.x < bx + 0.5 * BIRD_WIDTH
        in_y_range = (by < self.top_height_px or
                      by + BIRD_HEIGHT > WIN_HEIGHT - self.bottom_height_px)
        return in_x_range and in_y_range
    
    def is_cat_collision(self, cat_position):
        """Get whether the bird crashed into a pipe in this PipePair.

        Arguments:
        bird_position: The bird's position on screen, as a tuple in
            the form (X, Y).
        """
        cx, cy = cat_position
        in_x_range = cx - PIPE_WIDTH < self.x < cx + CAT_WIDTH
        in_y_range = (cy < self.top_height_px or
                      cy + BIRD_HEIGHT > WIN_HEIGHT - self.bottom_height_px)
        return in_x_range and in_y_range
    
    def is_dog_collision(self, dog_position):
        """Get whether the bird crashed into a pipe in this PipePair.

        Arguments:
        bird_position: The bird's position on screen, as a tuple in
            the form (X, Y).
        """
        dx, dy = dog_position
        in_x_range = dx - PIPE_WIDTH < self.x < dx + DOG_WIDTH
        in_y_range = (dy < self.top_height_px or
                      dy + BIRD_HEIGHT > WIN_HEIGHT - self.bottom_height_px)
        return in_x_range and in_y_range

def load_images():
    """Load all images required by the game and return a dict of them.

    The returned dict has the following keys:
    background: The game's background image.
    bird-wingup: An image of the bird with its wing pointing upward.
        Use this and bird-wingdown to create a flapping bird.
    bird-wingdown: An image of the bird with its wing pointing downward.
        Use this and bird-wingup to create a flapping bird.
    pipe-end: An image of a pipe's end piece (the slightly wider bit).
        Use this and pipe-body to make pipes.
    pipe-body: An image of a slice of a pipe's body.  Use this and
        pipe-body to make pipes.
    """

    def load_image(img_file_name):
        """Return the loaded pygame image with the specified file name.

        This function looks for images in the game's images folder
        (./images/).  All images are converted before being returned to
        speed up blitting.

        Arguments:
        img_file_name: The file name (including its extension, e.g.
            '.png') of the required image, without a file path.
        """
        file_name = os.path.join('.', 'images', img_file_name)
        img = pygame.image.load(file_name)
        # converting all images before use speeds up blitting
        img.convert()
        return img

    return {'background': load_image('background7.png'),
            'pipe-end': load_image('pipe_end.png'),
            'pipe-body': load_image('pipe_body.png'),            
            # images for animating the flapping bird -- animated GIFs are
            # not supported in pygame
            'bird-wingup': load_image('Silicon_wing_up.png'),
            'bird-wingdown': load_image('Silicon_wing_down.png'),
            'cat-wingup': load_image('OPV_wing_up.png'),
            'cat-wingdown': load_image('OPV_wing_down.png'),
            'dog-wingup': load_image('Perovskite_wing_up.png'),
            'dog-wingdown': load_image('Perovskite_wing_down.png'),
            'bang': load_image('bang4.png')}


def random_pipe_pair(pipe_end_img, pipe_body_img):
    """Return a PipePair with pipes of random height.

    The returned PipePair's surface will contain one bottom-up pipe
    and one top-down pipe.  The pipes will have a distance of
    BIRD_HEIGHT*3.
    Both passed images are assumed to have a size of (PIPE_WIDTH,
    PIPE_PIECE_HEIGHT).

    Arguments:
    pipe_end_img: The image to use to represent a pipe's endpiece.
    pipe_body_img: The image to use to represent one horizontal slice
        of a pipe's body.
    """
    surface = pygame.Surface((PIPE_WIDTH, WIN_HEIGHT), SRCALPHA)
    surface.convert()   # speeds up blitting
    surface.fill((0, 0, 0, 0))
    max_pipe_body_pieces = int(
        (WIN_HEIGHT -            # fill window from top to bottom
        int(3 * BIRD_HEIGHT + BIRD_HEIGHT / (2 + 0.5 * max(bird_score,  cat_score, dog_score))) - # make room for bird to fit through. decreases as scores increase
        3 * PIPE_PIECE_HEIGHT) / # 2 end pieces and 1 body piece for top pipe
        PIPE_PIECE_HEIGHT        # to get number of pipe pieces
    )
    bottom_pipe_pieces = randint(1, max_pipe_body_pieces)
    top_pipe_pieces = max_pipe_body_pieces - bottom_pipe_pieces
    # bottom pipe
    for i in range(1, bottom_pipe_pieces + 1):
        surface.blit(pipe_body_img, (0, WIN_HEIGHT - i*PIPE_PIECE_HEIGHT))
    bottom_pipe_end_y = WIN_HEIGHT - bottom_pipe_pieces*PIPE_PIECE_HEIGHT
    surface.blit(pipe_end_img, (0, bottom_pipe_end_y - PIPE_PIECE_HEIGHT))
    # top pipe
    for i in range(top_pipe_pieces):
        surface.blit(pipe_body_img, (0, i * PIPE_PIECE_HEIGHT))
    top_pipe_end_y = top_pipe_pieces * PIPE_PIECE_HEIGHT
    surface.blit(pipe_end_img, (0, top_pipe_end_y))
    # compensate for added end pieces
    bottom_pipe_pieces += 1
    top_pipe_pieces += 1
    return PipePair(surface, top_pipe_pieces, bottom_pipe_pieces)


def main():
    """The application's entry point.

    If someone executes this module (instead of importing it, for
    example), this function is called.
    """

    pygame.init()

    display_surface = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT), FULLSCREEN)
    pygame.display.set_caption('Flappy Solar Cell')

    clock = pygame.time.Clock()

    score_font = pygame.font.SysFont(None, 140, bold=True)  # default font
    high_score_font = pygame.font.SysFont(None, 80, bold=True)
    # the bird stays in the same x position, so BIRD_X is a constant
    BIRD_X = 0.45 * WIN_WIDTH
    CAT_X = 0.5 * WIN_WIDTH
    DOG_X = 0.6 * WIN_WIDTH
        
    #setting up the serial port - the first part refers to the port connected to the arduino. 9600 is the baud rate
    ser = serial.Serial(arduino_port, 9600)
    
    images = load_images()
    bird_score = 0
    cat_score = 0
    dog_score = 0
    BIRD_V = 100
    CAT_V = 100
    DOG_V = 100
    
    #pygame.time.set_timer(EVENT_NEWPIPE, PIPE_ADD_INTERVAL) replaced with varying timer in loop
    pipes = []
    time_since_last_pipe = 2000
    
    #fill high_scores with something to be able to sort and print
    high_scores = {0:[0,0],1:[1,1],2:[2,2],3:[3,3],4:[4,4],5:[5,5]}

    done = paused = False
    while not done:
        PIPE_ADD_INTERVAL = int(1800 + 3200 / (1 + 0.5 * max(bird_score, cat_score, dog_score)))    # milliseconds. decreases as scores increase

        # timer for adding new pipes
        if (pygame.time.get_ticks() - time_since_last_pipe > PIPE_ADD_INTERVAL):
            time_since_last_pipe = pygame.time.get_ticks()
            pygame.event.post(pygame.event.Event(EVENT_NEWPIPE))     
            
        # press esc to close and 'P' for pause. create new pipe if required
        for e in pygame.event.get():            
            if e.type == QUIT or (e.type == KEYUP and (e.key == K_ESCAPE or e.key == K_q)):
                done = True
                break
            elif e.type == KEYUP and e.key in (K_PAUSE, K_p):
                paused = not paused
            elif e.type == EVENT_NEWPIPE:
                pp = random_pipe_pair(images['pipe-end'], images['pipe-body'])
                pipes.append(pp)
        
        # wait until serail reads 'v' then takes the next three values as solar cell voltages
        oldBIRD_V = BIRD_V
        oldCAT_V = CAT_V
        oldDOG_V = DOG_V
        if ser.readline() == b'v\r\n':
            try:
                BIRD_V = int(ser.readline().decode("utf-8").replace("\r\n",""))
                CAT_V = int(ser.readline().decode("utf-8").replace("\r\n",""))
                DOG_V = int(ser.readline().decode("utf-8").replace("\r\n",""))
                #print(str(BIRD_V) + " " + str(CAT_V) + " " + str(DOG_V))
            except:
                BIRD_V = oldBIRD_V
                CAT_V = oldCAT_V
                DOG_V = oldDOG_V
                #print('nope')
                pass
        
        clock.tick(FPS)
        if paused:
            continue  # don't draw anything
        
        #convert voltages into into y coordinates
        bird_y = (BIRD_V - BIRD_MinV) / (BIRD_MaxV - BIRD_MinV) * WIN_HEIGHT
        cat_y =  (CAT_V - CAT_MinV) / (CAT_MaxV - CAT_MinV) * WIN_HEIGHT
        dog_y =  (DOG_V - DOG_MinV) / (DOG_MaxV - DOG_MinV) * WIN_HEIGHT  
        
        # fill surface then blitter small amount with background image. if entire surface blitter then RPi can't handel it on above ~500x500 pixels
        display_surface.fill((183,241,255))
        display_surface.blit(images['background'], (0,(WIN_HEIGHT - 178)))
        pygame.draw.circle(display_surface, (255,255,255), ((1300), (200)), (75))           
            
        # because pygame doesn't support animated GIFs, we have to
        # animate the flapping bird ourselves
        if pygame.time.get_ticks() % 500 >= 250:
            display_surface.blit(images['bird-wingup'], (BIRD_X, bird_y))
            display_surface.blit(images['cat-wingup'], (CAT_X, cat_y))
            display_surface.blit(images['dog-wingup'], (DOG_X, dog_y))
        else:
            display_surface.blit(images['bird-wingdown'], (BIRD_X, bird_y))
            display_surface.blit(images['cat-wingdown'], (CAT_X, cat_y))
            display_surface.blit(images['dog-wingdown'], (DOG_X, dog_y))

        # update and display scores
        for p in pipes:
            if p.x + PIPE_WIDTH < BIRD_X and not p.bird_score_counted:
                bird_score += 1
                p.bird_score_counted = True            
            if p.x + PIPE_WIDTH < CAT_X and not p.cat_score_counted:
                cat_score += 1
                p.cat_score_counted = True
            if p.x + PIPE_WIDTH < DOG_X and not p.dog_score_counted:
                dog_score += 1
                p.dog_score_counted = True
        
        #shift pipes along abit
        for p in pipes:
            p.x -= FRAME_ANIMATION_WIDTH
            if p.x <= -PIPE_WIDTH:  # PipePair is off screen
                pipes.remove(p)
            else:
                display_surface.blit(p.surface, (p.x, 0))
                
        # update and display running scores
        bird_score_surface = score_font.render(('Silicon: ' + str(bird_score)), True, (1, 1, 1))
        bird_score_x = 0.03*WIN_WIDTH #- bird_score_surface.get_width()/2
        display_surface.blit(bird_score_surface, (bird_score_x, 0.05 * WIN_HEIGHT))
        
        cat_score_surface = score_font.render(('OPV: ' + str(cat_score)), True, (1, 1, 1))
        cat_score_x = 0.03*WIN_WIDTH #- cat_score_surface.get_width()/2
        display_surface.blit(cat_score_surface, (cat_score_x, 0.18 * WIN_HEIGHT))
        
        dog_score_surface = score_font.render(('Perovskite: ' + str(dog_score)), True, (1, 1, 1))
        dog_score_x = 0.03*WIN_WIDTH #- cat_score_surface.get_width()/2
        display_surface.blit(dog_score_surface, (dog_score_x, 0.31 * WIN_HEIGHT))
        
        high_score_surface = high_score_font.render(('High Scores:'), True, (1, 1, 1))
        high_score_x = 0.03*WIN_WIDTH #- cat_score_surface.get_width()/2
        display_surface.blit(high_score_surface, (high_score_x, 0.5 * WIN_HEIGHT))
        # print high scores
        high_score_surface1 = high_score_font.render((str(sorted(high_scores.items(), key=operator.itemgetter(0))[-1][0]) + str(sorted(high_scores.items(), key=operator.itemgetter(0))[-1][1][1]) + str(sorted(high_scores.items(), key=operator.itemgetter(0))[-1][1][0])), True, (1, 1, 1))
        high_score_surface2 = high_score_font.render((str(sorted(high_scores.items(), key=operator.itemgetter(0))[-2][0]) + str(sorted(high_scores.items(), key=operator.itemgetter(0))[-2][1][1]) + str(sorted(high_scores.items(), key=operator.itemgetter(0))[-2][1][0])), True, (1, 1, 1))
        high_score_surface3 = high_score_font.render((str(sorted(high_scores.items(), key=operator.itemgetter(0))[-3][0]) + str(sorted(high_scores.items(), key=operator.itemgetter(0))[-3][1][1]) + str(sorted(high_scores.items(), key=operator.itemgetter(0))[-3][1][0])), True, (1, 1, 1))
        high_score_surface4 = high_score_font.render((str(sorted(high_scores.items(), key=operator.itemgetter(0))[-4][0]) + str(sorted(high_scores.items(), key=operator.itemgetter(0))[-4][1][1]) + str(sorted(high_scores.items(), key=operator.itemgetter(0))[-4][1][0])), True, (1, 1, 1))
        high_score_surface5 = high_score_font.render((str(sorted(high_scores.items(), key=operator.itemgetter(0))[-5][0]) + str(sorted(high_scores.items(), key=operator.itemgetter(0))[-5][1][1]) + str(sorted(high_scores.items(), key=operator.itemgetter(0))[-5][1][0])), True, (1, 1, 1))
        high_score_x = 0.03*WIN_WIDTH #- cat_score_surface.get_width()/2
        display_surface.blit(high_score_surface1, (high_score_x, 0.58 * WIN_HEIGHT))
        display_surface.blit(high_score_surface2, (high_score_x, 0.66 * WIN_HEIGHT))
        display_surface.blit(high_score_surface3, (high_score_x, 0.74 * WIN_HEIGHT))
        display_surface.blit(high_score_surface4, (high_score_x, 0.82 * WIN_HEIGHT))
        display_surface.blit(high_score_surface5, (high_score_x, 0.9 * WIN_HEIGHT))
         
        # check for collisions and update high_scores
        bird_pipe_collisions = [p.is_bird_collision((BIRD_X, bird_y)) for p in pipes]
        if (True in bird_pipe_collisions):
            if bird_score > 1:
                high_scores[bird_score] = [datetime.datetime.now().strftime('%H:%M:%S'), ' silicon ']
                print('Silicon crashed! ' + datetime.datetime.now().strftime('%H:%M:%S') + ' Score: %i' % bird_score)
            display_surface.blit(images['bang'], (BIRD_X, bird_y))
            bird_score = 0
            p.bird_score_counted = True
            
        cat_pipe_collisions = [p.is_bird_collision((CAT_X, cat_y)) for p in pipes]
        if (True in cat_pipe_collisions):
            if cat_score > 1:
                high_scores[cat_score] = [datetime.datetime.now().strftime('%H:%M:%S'), ' OPV ']
                print('OPV crashed! ' + datetime.datetime.now().strftime('%H:%M:%S') + ' Score: %i' % cat_score)
            display_surface.blit(images['bang'], (CAT_X, cat_y))
            cat_score = 0 
            p.cat_score_counted = True
        
        dog_pipe_collisions = [p.is_bird_collision((DOG_X, dog_y)) for p in pipes]
        if (True in dog_pipe_collisions):               
            if dog_score > 1:
                high_scores[dog_score] = [datetime.datetime.now().strftime('%H:%M:%S'), ' perovskite ']
                print('Perovskite crashed! ' + datetime.datetime.now().strftime('%H:%M:%S') + ' Score: %i' % dog_score)
            display_surface.blit(images['bang'], (DOG_X, dog_y))
            dog_score = 0
            p.dog_score_counted = True     

        pygame.display.update()
            
    pygame.quit()


if __name__ == '__main__':
    # If this module had been imported, __name__ would be 'flappybird'.
    # It was executed (e.g. by double-clicking the file), so call main.
    main()

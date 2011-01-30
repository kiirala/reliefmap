#!/usr/bin/python
# coding: utf-8

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL.shaders import *
import time
import math
import numpy
import ctypes
import pygame
#import pygame.image
from pygame.locals import *

resX,resY = (400,300 )
rotx, roty = (0, 0)
lastx, lasty = (0, 0)
rotview, distance, height = (0.0, 5.0, 0.0)

p_reliefmap = None
p_checker = None

boxShape = None
terrain = None

anaglyph = False

def quad(corner1, corner2, normal):
    c1 = numpy.array(corner1)
    c2 = numpy.array(corner2)
    tangent = c2 - c1
    bitangent = numpy.cross(normal, tangent)
    c3 = c2 + (bitangent - tangent) * 0.5
    c4 = c1 + (tangent - bitangent) * 0.5
    triangles = (0, 1, 2,
                 0, 3, 1)
    vertices = list(c1) + list(c2) + list(c3) + list(c4)
    n = list(normal / numpy.dot(normal, normal))
    normals = n * 4
    i = c4 - c1
    i = i / math.sqrt(numpy.dot(i, i))
    j = c3 - c1
    j = j / math.sqrt(numpy.dot(j, j))
    texcoords = (0.0, 0.0, 1.0, 1.0, 0.0, 1.0, 1.0, 0.0)
    tangents = (i[0], i[1], i[2],
                i[0], i[1], i[2],
                i[0], i[1], i[2],
                i[0], i[1], i[2])
    return (triangles, vertices, normals, texcoords, tangents)

def appendobj(orig, obj):
    return (orig[0] + tuple(map(lambda x: x + len(orig[1]) / 3, obj[0])),
            orig[1] + obj[1],
            orig[2] + obj[2],
            orig[3] + obj[3],
            orig[4] + obj[4])

def box(size):
    obj = quad((-size, size, size), (size, -size, size), (0.0, 0.0, 1.0))
    obj = appendobj(obj, quad((size, size, -size), (-size, -size, -size),
                              (0.0, 0.0, -1.0)))
    obj = appendobj(obj, quad((-size, size, -size), (size, size, size),
                              (0.0, 1.0, 0.0)))
    obj = appendobj(obj, quad((-size, -size, size), (size, -size, -size),
                              (0.0, -1.0, 0.0)))
    obj = appendobj(obj, quad((size, size, size), (size, -size, -size),
                              (1.0, 0.0, 0.0)))
    obj = appendobj(obj, quad((-size, size, -size), (-size, -size, size),
                              (-1.0, 0.0, 0.0)))
    return obj

def pyopengl_arrayfix(obj):
    arr_type = ctypes.c_double * len(obj[4])
    tangents = arr_type(0.0)
    for i in range(len(obj[4])):
        tangents[i] = obj[4][i]
    return (obj[0], obj[1], obj[2], obj[3], tangents)

def setTexture(texture, unit):
    glActiveTexture(unit)
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, texture)

def setUniform(program, name, value):
    loc = glGetUniformLocation(program, name)
    glUniform1i(loc, value)

def drawobj(obj, program):
    global colourmap, heightmap, normalmap
    glUseProgram(program)
    depthloc = glGetUniformLocation(program, "depth")
    glUniform1f(depthloc, 0.03)
    triangles, vertices, normals, texcoords, tangents = obj
    setTexture(colourmap, GL_TEXTURE0)
    setUniform(program, "texture", 0)
    setTexture(heightmap, GL_TEXTURE1)
    setUniform(program, "heightmap", 1)
    setTexture(normalmap, GL_TEXTURE2)
    setUniform(program, "normalmap", 2)
    glEnableClientState(GL_VERTEX_ARRAY)
    glEnableClientState(GL_NORMAL_ARRAY)
    glEnableClientState(GL_TEXTURE_COORD_ARRAY)
    glVertexPointer(3, GL_DOUBLE, 0, vertices)
    glNormalPointer(GL_DOUBLE, 0, normals)
    glTexCoordPointer(2, GL_DOUBLE, 0, texcoords)
    tangentloc = glGetAttribLocation(program, "tangent")
    if tangentloc >= 0:
        glEnableVertexAttribArray(tangentloc)
        glVertexAttribPointer(tangentloc, 3, GL_DOUBLE, GL_FALSE, 0, tangents)
    glDrawElements(GL_TRIANGLES, len(triangles), GL_UNSIGNED_INT, triangles)
    glDisableClientState(GL_VERTEX_ARRAY)
    glDisableClientState(GL_NORMAL_ARRAY)
    glDisableClientState(GL_TEXTURE_COORD_ARRAY)
    if tangentloc >= 0:
        glDisableVertexAttribArray(tangentloc)

def display( ):
    global boxShape, terrain, distance, rotview, height, rotx, roty, p_reliefmap, p_checker, anaglyph
    if boxShape is None:
        boxShape = pyopengl_arrayfix(box(1.0))
    if terrain is None:
        terrain = pyopengl_arrayfix(quad((-30, -2, 30), (30, -2, -30), (0, 1, 0)))
    glutSetWindow(window);
    glClearColor (1.0, 1.0, 1.0, 0.0)
    glClear (GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_CULL_FACE)

    def innerRender(xd):
        glLoadIdentity()
        glTranslate(xd, 0.0, 0.0)
        glRotate(math.atan(xd / distance) / math.pi * 180, 0.0, 1.0, 0.0)
        glTranslate(0.0, 0.0, -distance)
        glRotate(math.atan(height / 1.0) / math.pi * 180, 1.0, 0.0, 0.0)
        glRotate(rotview, 0.0, 1.0, 0.0)
        glLight(GL_LIGHT0, GL_POSITION, (0, 10, 0, 1.0))
        glLight(GL_LIGHT1, GL_POSITION, (-3, -1, 5, 1.0))
        glLight(GL_LIGHT2, GL_POSITION, (4, 0, -4, 1.0))

        drawobj(terrain, p_checker)
        glRotate(rotx, 0.0, 1.0, 0.0)
        glRotate(roty, 1.0, 0.0, 0.0)
        drawobj(boxShape, p_reliefmap)

    if not anaglyph:
        innerRender(0)
    else:
        dist = 0.04
        glColorMask(GL_TRUE, GL_FALSE, GL_FALSE, GL_TRUE)
        innerRender(dist)
        glClear(GL_DEPTH_BUFFER_BIT)
        glColorMask(GL_FALSE, GL_TRUE, GL_TRUE, GL_TRUE)
        innerRender(-dist)
        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)

    glFlush ()
    glutSwapBuffers()

def shaderFromSource(shadertype, source):
    shader = glCreateShader(shadertype)
    glShaderSource(shader, (source,))
    glCompileShader(shader)
    print glGetShaderInfoLog(shader)
    return shader

def programFromShaders(vert, frag):
    prog = glCreateProgram()
    glAttachShader(prog, vert)
    glAttachShader(prog, frag)
    glLinkProgram(prog)
    return prog

def load_shaders():
    global p_reliefmap, p_checker
    p_reliefmap = loadShader("reliefmap.glsl")
    p_checker = loadShader("checker.glsl")

def loadShader(filename):
    inp = open(filename, "r")
    pfrag = ""
    pvert = ""
    mode = 0
    for line in inp:
        if line.startswith("["):
            if line.startswith("[VertexShader]"):
                mode = 1
            elif line.startswith("[FragmentShader]"):
                mode = 2
            else:
                mode = 0
        else:
            if mode == 1:
                pvert += line
            elif mode == 2:
                pfrag += line
    svert = shaderFromSource(GL_VERTEX_SHADER, pvert)
    sfrag = shaderFromSource(GL_FRAGMENT_SHADER, pfrag)
    program = programFromShaders(svert, sfrag)
    print glGetProgramInfoLog(program)
    if glGetProgramiv(program, GL_LINK_STATUS) != GL_TRUE:
        print "Loading shaders failed."
        exit(1)
    return program

def load_texture(fname):
    img = pygame.image.load(fname)
    data = pygame.image.tostring(img, "RGB", True)
    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
    glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
    glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, img.get_width(), img.get_height(),
                 0, GL_RGB, GL_UNSIGNED_BYTE, data)
    return texture

def load_textures():
    colour = load_texture("relief_colour.png")
    #height = load_texture("cube_heightmap.png")
    #normal = load_texture("cube_normalmap.png")
    height = load_texture("relief_height.png")
    normal = load_texture("relief_normal.png")
    return (colour, height, normal)

def setupLight():
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_LIGHT1)
    glEnable(GL_LIGHT2)

def defaultProjection():
    global resX, resY
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, float(resX) / float(resY), 0.1, 100)
    glMatrixMode(GL_MODELVIEW)

def reshape(width, height):
    global resX, resY
    resX = width
    resY = height
    glViewport(0, 0, width, height)
    defaultProjection()

def mouseClick(button, state, x, y):
    global lastx, lasty
    if (state == GLUT_DOWN):
        lastx = x
        lasty = y

def mouseMotion(xpos, ypos):
    global rotx,roty, lastx, lasty
    rotx += xpos - lastx
    roty += ypos - lasty
    lastx = xpos
    lasty = ypos
    glutPostRedisplay()

def keyPress(asc, xpos, ypos):
    global anaglyph
    #print "'%s' 0x%2x %3d" % (asc, ord(asc), ord(asc))
    if asc == '\x1b':
        exit(0)
    elif asc == 'a':
        anaglyph = not anaglyph
        glutPostRedisplay()

def specialPress(key, xpos, ypos):
    global rotview, distance, height
    if key == GLUT_KEY_LEFT:
        rotview += 1
    elif key == GLUT_KEY_RIGHT:
        rotview -= 1
    elif key == GLUT_KEY_UP and distance > 0:
        distance -= min(distance, 0.1)
    elif key == GLUT_KEY_DOWN and distance < 50:
        distance += 0.1
    elif key == GLUT_KEY_PAGE_DOWN and height > 0:
        height -= min(height, 0.1)
    elif key == GLUT_KEY_PAGE_UP and height < 50:
        height += 0.1
    glutPostRedisplay()

if __name__ == "__main__":
    pygame.init()

    glutInit([])
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)

    glutInitWindowSize(resX, resY)

    #glutInitWindowPosition(0, 0)
    window = glutCreateWindow("reliefmap")
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutMotionFunc(mouseMotion)
    glutMouseFunc(mouseClick)
    glutKeyboardFunc(keyPress)
    glutSpecialFunc(specialPress)

    for name in (GL_VENDOR,GL_RENDERER,GL_VERSION,GL_SHADING_LANGUAGE_VERSION):
        print name,glGetString(name)

    load_shaders()
    colourmap, heightmap, normalmap = load_textures()
    setupLight()

    reshape(resX, resY)

    glutMainLoop()

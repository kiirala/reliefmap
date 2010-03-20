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

p_reliefmap = None
boxShape = None

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
    obj = appendobj(obj, quad((size, -size, -size), (-size, size, -size),
                              (0.0, 0.0, -1.0)))
    for tbl in obj:
        print tbl
    obj = appendobj(obj, quad((-size, size, -size), (size, size, size),
                              (0.0, 1.0, 0.0)))
    obj = appendobj(obj, quad((size, -size, size), (-size, -size, -size),
                              (0.0, -1.0, 0.0)))
    obj = appendobj(obj, quad((size, size, size), (size, -size, -size),
                              (1.0, 0.0, 0.0)))
    obj = appendobj(obj, quad((-size, -size, -size), (-size, size, size),
                              (-1.0, 0.0, 0.0)))
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
    glUseProgram(p_reliefmap)
    depthloc = glGetUniformLocation(p_reliefmap, "depth")
    glUniform1f(depthloc, 0.05)
    triangles, vertices, normals, texcoords, tangents = obj
    tangentloc = glGetAttribLocation(program, "tangent")
    setTexture(colourmap, GL_TEXTURE0)
    setUniform(p_reliefmap, "texture", 0)
    setTexture(heightmap, GL_TEXTURE1)
    setUniform(p_reliefmap, "heightmap", 1)
    setTexture(normalmap, GL_TEXTURE2)
    setUniform(p_reliefmap, "normalmap", 2)
    glEnableClientState(GL_VERTEX_ARRAY)
    glEnableClientState(GL_NORMAL_ARRAY)
    glEnableClientState(GL_TEXTURE_COORD_ARRAY)
    glEnableVertexAttribArray(tangentloc)
    glVertexPointer(3, GL_DOUBLE, 0, vertices)
    glNormalPointer(GL_DOUBLE, 0, normals)
    glTexCoordPointer(2, GL_DOUBLE, 0, texcoords)
    glVertexAttribPointer(tangentloc, 3, GL_DOUBLE, GL_FALSE, 0, tangents)
    glDrawElements(GL_TRIANGLES, len(triangles), GL_UNSIGNED_INT, triangles)
    glDisableClientState(GL_VERTEX_ARRAY)
    glDisableClientState(GL_NORMAL_ARRAY)
    glDisableClientState(GL_TEXTURE_COORD_ARRAY)
    glDisableVertexAttribArray(tangentloc)

def display( ):
    global boxShape, rotx, roty
    if boxShape is None:
        boxShape = box(1.0)
    glutSetWindow(window);
    glClearColor (0.3, 0.7, 0.7, 0.0)
    glClear (GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_CULL_FACE)

    glLoadIdentity()
    glTranslate(0.0, 0.0, -5.0)
    glRotate(rotx, 0.0, 1.0, 0.0)
    glRotate(roty, 1.0, 0.0, 0.0)
    drawobj(boxShape, p_reliefmap)

    glFlush ()
    glutSwapBuffers()

def shaderFromSource(shadertype, source):
    shader = glCreateShader(shadertype)
    glShaderSource(shader, (source,))
    glCompileShader(shader)
    return shader

def programFromShaders(vert, frag):
    prog = glCreateProgram()
    glAttachShader(prog, vert)
    glAttachShader(prog, frag)
    glLinkProgram(prog)
    return prog

def load_shaders():
    global p_reliefmap
    inp = open("reliefmap.glsl", "r")
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
    p_reliefmap = programFromShaders(svert, sfrag)
    print glGetProgramInfoLog(p_reliefmap)
    if glGetProgramiv(p_reliefmap, GL_LINK_STATUS) != GL_TRUE:
        print "Loading shaders failed."
        exit(1)

def load_texture(fname):
    img = pygame.image.load(fname)
    data = pygame.image.tostring(img, "RGB")
    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, img.get_width(), img.get_height(),
                 0, GL_RGB, GL_UNSIGNED_BYTE, data)
    return texture

def load_textures():
    colour = load_texture("relief_colour.png")
    height = load_texture("relief_height.png")
    normal = load_texture("relief_normal.png")
    return (colour, height, normal)

def setupLight():
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLight(GL_LIGHT0, GL_POSITION, (0, 1, 0, 0))

def reshape(width, height):
    global resX, resY
    resX = width
    resY = height
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, float(resX) / float(resY), 0.1, 10)

    glMatrixMode(GL_MODELVIEW)

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

if __name__ == "__main__":
    pygame.init()

    glutInit([])
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)

    glutInitWindowSize(resX, resY)

    #glutInitWindowPosition(0, 0)
    window = glutCreateWindow("hello")
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutMotionFunc(mouseMotion)
    glutMouseFunc(mouseClick)

    for name in (GL_VENDOR,GL_RENDERER,GL_VERSION,GL_SHADING_LANGUAGE_VERSION):
        print name,glGetString(name)

    load_shaders()
    colourmap, heightmap, normalmap = load_textures()
    setupLight()

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, float(resX) / float(resY), 0.1, 10)

    glMatrixMode(GL_MODELVIEW)

    glutMainLoop()

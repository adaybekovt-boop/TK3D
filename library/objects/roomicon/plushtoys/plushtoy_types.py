"""Генерация мягких игрушек: медведь, зайчик, пингвин, утёнок."""

import bpy
import math
import random
import mathutils

from helpers import (
    create_sphere, create_ellipsoid, create_cone, create_droopy_ear,
    add_subdivision, mat_plush, mat_eye,
    PLUSH_COLORS, BELLY_COLORS, BEAR_COLORS,
)


PLUSHTOY_TYPES = {
    'bear': {},
    'bunny': {},
    'penguin': {},
    'duck': {},
}


def _pick_color(rng, palette=None):
    """Pick random color name from palette or all."""
    if palette:
        return rng.choice(palette)
    return rng.choice(list(PLUSH_COLORS.keys()))


def _add_eyes(objects, head_y, head_z, head_r, eye_r, spread=0.35):
    """Add two eyes on the front of the head."""
    eye_mat = mat_eye()
    for side in (-1, 1):
        eye = create_sphere(
            "Eye", eye_r,
            cx=side * head_r * spread,
            cy=-head_r * 0.85,
            cz=head_z + head_r * 0.15,
        )
        eye.data.materials.append(eye_mat)
        objects.append(eye)


def _add_nose(objects, head_z, head_r, nose_r, color):
    """Add a small nose sphere."""
    nose = create_sphere(
        "Nose", nose_r,
        cy=-head_r * 0.95,
        cz=head_z - head_r * 0.1,
    )
    nose_mat = mat_plush("M_PlushNose", color, roughness=0.6)
    nose.data.materials.append(nose_mat)
    objects.append(nose)


def _make_bear(rng):
    """Teddy bear."""
    scale = rng.uniform(0.08, 0.12)
    color_name = _pick_color(rng, BEAR_COLORS)
    body_color = PLUSH_COLORS[color_name]
    belly_color = BELLY_COLORS[color_name]

    body_mat = mat_plush(f"M_PlushBear_{color_name}", body_color)
    belly_mat = mat_plush(f"M_PlushBearBelly_{color_name}", belly_color)

    objects = []

    # Body
    body = create_ellipsoid("Body", scale, scale * 0.85, scale * 1.1,
                            cz=scale * 1.1)
    body.data.materials.append(body_mat)
    add_subdivision(body, 2)
    objects.append(body)

    # Belly patch
    belly = create_ellipsoid("Belly", scale * 0.55, scale * 0.3, scale * 0.65,
                             cy=-scale * 0.55, cz=scale * 1.1)
    belly.data.materials.append(belly_mat)
    objects.append(belly)

    # Head
    head_z = scale * rng.uniform(2.3,2.7)
    head_r = scale * rng.uniform(0.7,0.8)
    head = create_sphere("Head", head_r, cz=head_z)
    head.data.materials.append(body_mat)
    add_subdivision(head, 2)
    objects.append(head)

    # Muzzle
    muzzle = create_ellipsoid("Muzzle", head_r * 0.4, head_r * 0.35, head_r * 0.3,
                              cy=-head_r * 0.7, cz=head_z - head_r * 0.15)
    muzzle.data.materials.append(belly_mat)
    objects.append(muzzle)

    # Ears
    ear_r = head_r * rng.uniform(0.3,0.4)
    for side in (-1, 1):
        ear = create_sphere("Ear", ear_r,
                            cx=side * head_r * 0.7,
                            cz=head_z + head_r * 0.7)
        ear.data.materials.append(body_mat)
        objects.append(ear)

    # Eyes & nose
    _add_eyes(objects, 0, head_z, head_r, head_r * 0.1)
    _add_nose(objects, head_z, head_r, head_r * 0.12, (0.15, 0.08, 0.05, 1))

    # Arms
    arm_r = scale * 0.3
    arm_len = scale * rng.uniform(0.5,0.8)
    arm_angle = rng.uniform(0.4,0.6)
    for side in (-1, 1):
        arm = create_ellipsoid("Arm", arm_r, arm_r * 0.8, arm_len)
        arm.location = (side * scale * 0.95,0,scale * 1.2)
        arm.data.materials.append(body_mat)
        arm.rotation_euler = (0, -side * arm_angle, 0)
        objects.append(arm)

    # Legs
    leg_r = scale * 0.35
    for side in (-1, 1):
        leg = create_ellipsoid("Leg", leg_r * 0.8, leg_r * 1.5, leg_r * 0.8)
        leg.location = (side * scale * 0.55, -scale * 0.55,leg_r * 0.8)
        leg.data.materials.append(body_mat)
        leg.rotation_euler = (-math.pi/8, 0, side*math.pi/7)
        objects.append(leg)
    # Feet
    foot_r = scale * 0.35
    for side in (-1, 1):
        foot = create_ellipsoid("Foot", foot_r * 0.5, foot_r, foot_r * 0.8)
        foot.location = (side * scale * 0.65, -scale * 0.9,foot_r * 1.6)
        foot.data.materials.append(body_mat)
        foot.rotation_euler = (side * math.pi/3, math.pi/7, math.pi/2)
        objects.append(foot)

    return objects


def _make_bunny(rng):
    """Bunny with long ears."""
    scale = rng.uniform(0.07, 0.11)
    color_name = rng.choice(['white', 'cream', 'grey', 'pink', 'light_brown'])
    body_color = PLUSH_COLORS[color_name]
    belly_color = BELLY_COLORS[color_name]

    body_mat = mat_plush(f"M_PlushBunny_{color_name}", body_color)
    belly_mat = mat_plush(f"M_PlushBunnyBelly_{color_name}", belly_color)

    objects = []

    # Body (rounder than bear)
    body = create_ellipsoid("Body", scale * 0.9, scale * 0.8, scale * 1.0,
                            cz=scale * 1.0)
    body.data.materials.append(body_mat)
    add_subdivision(body, 2)
    objects.append(body)

    # Belly
    belly = create_ellipsoid("Belly", scale * 0.5, scale * 0.25, scale * 0.55,
                             cy=-scale * 0.5, cz=scale * 1.0)
    belly.data.materials.append(belly_mat)
    objects.append(belly)

    # Head
    head_z = scale * 2.3
    head_r = scale * 0.7
    head = create_sphere("Head", head_r, cz=head_z)
    head.data.materials.append(body_mat)
    add_subdivision(head, 2)
    objects.append(head)

    # Long ears
    ear_len = scale * rng.uniform(1.2, 1.6)
    ear_w = scale * 0.2

    for side in (-1, 1):
        ear_cx = side * head_r * 0.4
        ear_cz = head_z + head_r*0.8
        tilt = (rng.uniform(-0.3, 0.8), side * rng.uniform(0.1, 0.45), 0)

        # Droopy ear — верхняя часть свисает
        droop = rng.uniform(0.6, 1.0)
        ear = create_droopy_ear("Ear", ear_w, ear_w * 0.5, ear_len, droop_amount=droop, droop_start=-0.4)
        ear.location = (ear_cx,0,ear_cz)
        ear.data.materials.append(body_mat)
        ear.rotation_euler = tilt
        objects.append(ear)

    # Eyes & nose
    _add_eyes(objects, 0, head_z, head_r, head_r * 0.1)
    _add_nose(objects, head_z, head_r, head_r * 0.1, (0.75, 0.45, 0.45, 1))

    # Arms
    for side in (-1, 1):
        arm = create_ellipsoid("Arm", scale * 0.22, scale * 0.2, scale * 0.55)
        arm.location = (side * scale * 0.6, 0,scale * 1.5)
        arm.data.materials.append(body_mat)
        arm.data.transform(mathutils.Matrix.Translation((0,0,scale * 0.55)))
        arm.rotation_euler = (0, side * rng.uniform(2,2.8), 0)
        objects.append(arm)

    # Legs
    for side in (-1, 1):
        leg = create_ellipsoid("Leg", scale * 0.3, scale * 0.5, scale * 0.25,
                               cx=side * scale * 0.35,
                               cy=-scale * 0.5,
                               cz=scale * 0.25)
        leg.rotation_euler = (0,0,side*math.pi/5)
        leg.data.materials.append(body_mat)
        objects.append(leg)

    # Tail (small puff)
    tail = create_sphere("Tail", scale * 0.2, cy=scale * 0.75, cz=scale * 0.7)
    tail.data.materials.append(belly_mat)
    objects.append(tail)

    return objects


def _make_penguin(rng):
    """Penguin — oval body, black/white."""
    scale = rng.uniform(0.08, 0.12)

    body_mat = mat_plush("M_PlushPenguinBody", (0.08, 0.08, 0.1, 1))
    belly_mat = mat_plush("M_PlushPenguinBelly", (0.92, 0.92, 0.9, 1))
    beak_color = rng.choice([
        (0.9, 0.6, 0.1, 1),   # orange
        (0.85, 0.45, 0.1, 1),  # dark orange
    ])
    feet_mat = mat_plush("M_PlushPenguinFeet", beak_color, roughness=0.7)

    objects = []

    # Body (tall oval)
    body = create_ellipsoid("Body", scale * 0.8, scale * 0.7, scale * 1.3,
                            cz=scale * 1.3)
    body.data.materials.append(body_mat)
    add_subdivision(body, 2)
    objects.append(body)

    # Belly (white front)
    belly = create_ellipsoid("Belly", scale * 0.55, scale * 0.3, scale * 0.95,
                             cy=-scale * 0.4, cz=scale * 1.15)
    belly.data.materials.append(belly_mat)
    objects.append(belly)

    # Head
    head_z = scale * 2.8
    head_r = scale * 0.6
    head = create_sphere("Head", head_r, cz=head_z)
    head.data.materials.append(body_mat)
    add_subdivision(head, 2)
    objects.append(head)

    # White face patch
    face = create_ellipsoid("Face", head_r * 0.55, head_r * 0.3, head_r * 0.5,
                            cy=-head_r * 0.5, cz=head_z)
    face.data.materials.append(belly_mat)
    objects.append(face)

    # Eyes
    _add_eyes(objects, 0, head_z, head_r, head_r * 0.1, spread=0.3)

    # Beak
    beak = create_cone("Beak", scale * 0.14, scale * 0.2,
                       cy=-head_r * 0.9, cz=head_z - head_r * 0.1)
    beak.rotation_euler = (0*math.pi / 2, 0, 0)
    beak_mat = mat_plush("M_PlushPenguinBeak", beak_color, roughness=0.6)
    beak.data.materials.append(beak_mat)
    objects.append(beak)

    # Flippers
    tilt = rng.uniform(1,3)
    flip_scale = scale * rng.uniform(1.2,1.7)
    for side in (-1, 1):
        flip = create_ellipsoid("Flipper", flip_scale * 0.15, flip_scale * 0.1, flip_scale * 0.6)
        flip.location = (side * scale * 0.60,0,scale*2)
        flip.data.transform(mathutils.Matrix.Translation((0,0,flip_scale * 0.55)))
        flip.data.materials.append(body_mat)
        flip.rotation_euler = (0, side * tilt, 0)
        objects.append(flip)

    # Feet
    for side in (-1, 1):
        foot = create_ellipsoid("Foot", scale * 0.25, scale * 0.35, scale * 0.08,
                                cx=side * scale * 0.3,
                                cy=-scale * 0.15,
                                cz=scale * 0.08)
        foot.data.materials.append(feet_mat)
        objects.append(foot)

    empty = bpy.data.objects.new('PenguinRoot',None)
    empty.empty_display_size = 0.01
    for o in objects:
        o.parent = empty
    empty.rotation_euler = (-math.pi/2,.15,0)
    empty.location = (0,0,scale*0.35)
    return [empty] + objects

    return objects


def _make_duck(rng):
    """Rubber duck style plush."""
    scale = rng.uniform(0.07, 0.10)
    yellow = rng.choice([
        (0.92, 0.82, 0.15, 1),
        (0.95, 0.75, 0.10, 1),
        (0.88, 0.78, 0.20, 1),
    ])

    body_mat = mat_plush("M_PlushDuck", yellow)
    beak_color = (0.9, 0.5, 0.05, 1)

    objects = []

    # Body (round, slightly flat)
    body = create_ellipsoid("Body", scale * 1.0, scale * 0.85, scale * 0.8,
                            cz=scale * 0.8)
    body.data.materials.append(body_mat)
    add_subdivision(body, 2)
    objects.append(body)

    # Head
    head_z = scale * 2.0
    head_r = scale * rng.uniform(0.5,0.7)
    head = create_sphere("Head", head_r, cz=head_z)
    head.data.materials.append(body_mat)
    add_subdivision(head, 2)
    objects.append(head)

    # Eyes
    _add_eyes(objects, 0, head_z, head_r, head_r * 0.12, spread=0.4)

    # Beak (flat wide)
    beak_scale = scale * rng.uniform(1,1.4)
    beak = create_ellipsoid("Beak", beak_scale * 0.2, beak_scale * 0.35, beak_scale * 0.08,
                            cy=-head_r * 0.9,
                            cz=head_z - head_r * 0.2)
    beak_mat = mat_plush("M_PlushDuckBeak", beak_color, roughness=0.6)
    beak.data.materials.append(beak_mat)
    objects.append(beak)

    # Wings
    for side in (-1, 1):
        wing = create_ellipsoid("Wing", scale * 0.15, scale * 0.4, scale * 0.5)
        wing.location = (side * scale * 0.65,scale * 0.1,scale * 1.3)
        wing.data.transform(mathutils.Matrix.Translation((0,0,scale * 0.5)))
        wing.data.materials.append(body_mat)
        wing.rotation_euler = (0.2, side * 2.3, 0)
        objects.append(wing)

    # Tail (small upward puff)
    #tail = create_ellipsoid("Tail", scale * 0.3, scale * 0.5, scale * 0.3, cy=scale * 0.8, cz=scale )
    tail = create_cone("Tail", scale * 0.4, scale * 0.5)#, scale * 0.3, cy=scale * 0, cz=scale*0 )
    tail.location = (0,scale*0.7,scale*0.8)
    tail.data.materials.append(body_mat)
    tail.rotation_euler = (-math.pi/2,0,0)
    objects.append(tail)

    return objects


_MAKERS = {
    'bear': _make_bear,
    'bunny': _make_bunny,
    'penguin': _make_penguin,
    'duck': _make_duck,
}


def generate_plushtoy(seed, subtype='bear'):
    """Generate a plush toy. Returns list of objects."""
    rng = random.Random(seed)
    maker = _MAKERS.get(subtype, _make_bear)
    return maker(rng)

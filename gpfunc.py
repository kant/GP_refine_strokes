from .utils import *
import bpy
import mathutils
from mathutils import Vector
from math import acos, degrees
from mathutils import geometry
import numpy as np

### -- GET STROKES FILTERS --

def get_layers(target='SELECT'):
    '''
    Return an iterable list of layer according to keywords target string
    SELECT (default), ACTIVE, ALL, SIDE_SELECT, UNRESTRICTED
    Return empty list if nothing found
    '''
    if not bpy.context.object.type == 'GPENCIL': return []
    if not bpy.context.object.data.layers.active: return []
    
    if not target or target == 'SELECT':# iterable with all selected layer (dopesheet)
        # return [l for l in bpy.context.object.data.layers if l.select and not l.hide and not l.lock]
        ## seems it can sometimes bug when there is an active that is not selected (should be selected) 
        return [l for l in bpy.context.object.data.layers if l ==  bpy.context.object.data.layers.active and not l.hide and not l.lock or l.select and not l.hide and not l.lock]

    elif target == 'ACTIVE':# iterable with only active layer
        return [bpy.context.object.data.layers.active]

    elif target == 'ALL': # all visible and unlocked layers iterable
        return [l for l in bpy.context.object.data.layers if not l.hide and not l.lock]

    elif target == 'SIDE_SELECT':# iterable with all selected layer except active
        if bpy.context.object.data.layers.active and len([l for l in bpy.context.object.data.layers if l.select and not l.hide and not l.lock]) > 1:
            return [l for l in bpy.context.object.data.layers if l.select and not l.hide and not l.lock and l != bpy.context.object.data.layers.active]
    
    elif target == 'UNRESTRICTED': # all layers iterable (everything)
        return bpy.context.object.data.layers

    return []

def get_frames(layer, target='ACTIVE'):
    '''
    Get a layer and return active frame or all frame as iterable
    ACTIVE default, ALL, SELECT, 
    Return empty list if nothing found
    '''
    if not layer.active_frame:return []

    if not target or target == 'ACTIVE':#iterable with active frame
        return  [layer.active_frame]
    
    elif target == 'ALL':#iterable of all frames in layer
        return layer.frames
    
    elif target == 'SELECT':#iterable of all selected frames in layer
        return [f for f in layer.frames if f.select]

    return []

def get_strokes(frame, target='SELECT'):
    '''
    Return an iterable list of layer according to keywords target string
    SELECT (default), ALL, LAST
    Return empty list if nothing found
    '''
    if not len(frame.strokes):return []
    
    if not target or target == 'SELECT':
        return  [s for s in frame.strokes if s.select]
    
    elif target == 'ALL':
        return frame.strokes
    
    elif target == 'LAST':
        # index is -1 or 0 if draw on back)
        return [frame.strokes[get_last_index()]]
    
    return []  

def strokelist(t_layer='ALL', t_frame='ACTIVE', t_stroke='SELECT'):
    '''
    Quickly return a strokelist according to given filters
    By default - All accessible on viewport : visible and unlocked
    '''
    ## TODO: when stroke is LAST and layer is ALL it can be the last of all layers, priority must be set to active layer.
    
    # superBAD - WRONG: (not flattened) : [[[s for s in get_strokes(f, target=t_stroke)] for f in get_frames(l, target=t_frame)] for l in get_layers(target=t_layer)][0][0]

    # itertool not tested enough, flatenned twice like this need speed tests...
    """ import itertools# un-nesting triple comprehension list
    turbolist = [[[s for s in get_strokes(f, target=t_stroke)] for f in get_frames(l, target=t_frame)] for l in get_layers(target=t_layer)]
    flattened = list(itertools.chain.from_iterable(turbolist))
    all_strokes = list(itertools.chain.from_iterable(flattened)) """

    all_strokes = []
    for l in get_layers(target=t_layer):
        for f in get_frames(l, target=t_frame):
            for s in get_strokes(f, target=t_stroke):
                all_strokes.append(s)

    return all_strokes

def get_last_stroke(context=None):
    '''return last stroke (first if )'''
    if not context:
        context=bpy.context
    
    return bpy.context.object.data.layers.active.active_frame.strokes[get_last_index(context)]

def selected_strokes():
    strokes = []
    for l in bpy.context.object.data.layers:
        if not l.hide and not l.lock:
            for s in l.active_frame.strokes:
                if s.select:
                    strokes.append(s)
    return(strokes)

### -- FUNCTIONS --

def get_tgts(context=None):
    '''return a tuple with the 3 pref target (layers, frame, stroke)'''
    if not context:
        context = bpy.context
    pref = context.scene.gprsettings
    return pref.layer_tgt, pref.frame_tgt, pref.stroke_tgt


def get_last_index(context=None):
    if not context:
        context = bpy.context
    return 0 if context.tool_settings.use_gpencil_draw_onback else -1


## -- overall attributes

#TODO use a foreach_set on points for speed
## Line attributes
def gp_add_line_attr(attr, amount, t_layer='SELECT', t_frame='ACTIVE', t_stroke='SELECT'):
    '''Get a stroke attribut, an int to Add, target filters'''
    for s in strokelist(t_layer=t_layer, t_frame=t_frame, t_stroke=t_stroke):
        setattr(s, attr, getattr(s, attr) + amount)

def gp_set_line_attr(attr, amount, t_layer='SELECT', t_frame='ACTIVE', t_stroke='SELECT'):
    for s in strokelist(t_layer=t_layer, t_frame=t_frame, t_stroke=t_stroke):
        setattr(s, attr, amount)

## Points attributes

def gp_add_attr(attr, amount, t_layer='SELECT', t_frame='ACTIVE', t_stroke='SELECT'):
    '''Get a point attribut, an int to Add, target filters'''
    for s in strokelist(t_layer=t_layer, t_frame=t_frame, t_stroke=t_stroke):
        for p in s.points:
            setattr(p, attr, getattr(p, attr) + amount)
            
def gp_set_attr(attr, amount, t_layer='SELECT', t_frame='ACTIVE', t_stroke='SELECT'):
    for s in strokelist(t_layer=t_layer, t_frame=t_frame, t_stroke=t_stroke):
        for p in s.points:
            setattr(p, attr, amount)

## Point vertex color

def gp_add_vg_alpha(amount, t_layer='SELECT', t_frame='ACTIVE', t_stroke='SELECT'):
    '''Get a point attribut, an int to Add, target filters'''
    for s in strokelist(t_layer=t_layer, t_frame=t_frame, t_stroke=t_stroke):
        for p in s.points:
            p.vertex_color[-1] += amount # (*p.vertex_color[:3], p.vertex_color[-1] + amount)

def gp_set_vg_alpha(amount, t_layer='SELECT', t_frame='ACTIVE', t_stroke='SELECT'):
    '''Get a point attribut, an int to Add, target filters'''
    for s in strokelist(t_layer=t_layer, t_frame=t_frame, t_stroke=t_stroke):
        for p in s.points:
            p.vertex_color[-1] = amount

## -- thinner tips

def abs_thinner_tip(s, tip_len=5, middle=0):
    '''
    Get a stroke and a number of point to make the interpolation
    give weird results
    '''
    e = len(s.points)
    for j, pt in enumerate(s.points):
        if j <= tip_len:
            normval = (j - 0) / (tip_len - 0)
            # print("j", j)#Dbg
            # print("normval", normval)#Dbg
            pt.pressure = normval
        if e <= tip_len:
            normval = (e - 0) / (tip_len - 0)
            # print("e", e)#Dbg
            # print("normval", normval)#Dbg
            pt.pressure = normval
        if middle and j > tip_len and e > tip_len:
            pt.pressure = middle
        e -= 1

def get_tip_from_percentage(s, tip_len=20, variance=0):
    '''
    Get a stroke and percentage
    return points number and number of points given a percentage from tip to middle of stroke (100%)
    '''
    p_num = len(s.points)#total number of points
    # limit = p_num//2#middle of the points
    # if limit < 2:
    if p_num < 4:
        print ('Not enough points to thin tip correctly')
        return
    if variance:
        import random
        tip_len = min(max(tip_len + random.randint(-variance, variance), 5),100)

    # thin_range = int( limit * tip_len/100)+1 #unnacurate percentage (of half the line) in point number
    thin_range = int(p_num * tip_len/100)+1 #unnacurate percentage in point number
    print(f'zone: {thin_range}/{p_num}')#Dbg
    return thin_range

def reshape_rel_thinner_tip_percentage(s, tip_len=10, variance=0):
    '''
    Make points's pressure of strokes thinner by a point number percentage value (on total)
    value is a percentage (of half a line min 10 percent, max 100)
    variance randomize the tip_len by given value (positive or negative)
    '''
    thin_range = get_tip_from_percentage(s, tip_len=tip_len, variance=variance)
    # Get pressure of point to fade from as reference. 
    #+1 To get one further point as a reference but dont affect it (no change if relaunch except if variance).
    start_max = s.points[thin_range+1].pressure 
    end_max = s.points[-thin_range-1].pressure  #-1 Same stuff
    for i in range(thin_range):
        # print(i, 'start ->', transfer_value(i, 0, thin_range, 0.1, start_max) )
        # print(i, 'end ->', transfer_value(i, 0, thin_range, 0.1, end_max) )
        s.points[i].pressure = transfer_value(i, 0, thin_range, 0.1, start_max)
        s.points[-(i+1)].pressure = transfer_value(i, 0, thin_range, 0.1, end_max)

    #average value ?
    """ # get pressure of average max...
    import statistics
    pressure_list = [p.pressure for p in s.points if p.pressure > 0.1]
    if not pressure_list:
        pressure_list = [p.pressure for p in s.points if p.pressure]
    average = statistics.mean(pressure_list)"""
    return 0

def reshape_abs_thinner_tip_percentage(s, tip_len=10, variance=0):
    '''
    Make points's pressure of strokes thinner by a point number percentage value (on total)
    All stroke will get max value
    '''
    thin_range = get_tip_from_percentage(s, tip_len=tip_len, variance=variance)
    max_pressure = max([p.pressure for p in s.points])
    for i in range(thin_range):#TODO : Transfer based on a curve to avoid straight fade.
        s.points[i].pressure = transfer_value(i, 0, thin_range, 0.1, max_pressure)
        s.points[-(i+1)].pressure = transfer_value(i, 0, thin_range, 0.1, max_pressure)

def info_pressure(t_layer='ACTIVE', t_frame='ACTIVE', t_stroke='SELECT'):
    '''print the pressure of targeted strokes'''
    print('\nPressure list:')
    for s in strokelist(t_layer=t_layer, t_frame=t_frame, t_stroke=t_stroke):
        print(['{:.3f}'.format(p.pressure) for p in s.points])


s_attrs = [
'line_width',
'hardness',
'material_index',
'uv_scale',
'draw_cyclic',
'aspect',
'display_mode',
]
# all stroke dir: ['bound_box_max', 'bound_box_min', 'display_mode', 'draw_cyclic', 'end_cap_mode', 'groups', 'hardness', 'is_nofill_stroke', 'line_width', 'material_index', 'points', 'select', 'start_cap_mode', 'triangles', 'uv_rotation', 'uv_scale', 'uv_translation', 'vertex_color_fill']

p_attrs = ['co', 
'pressure', 
'strength', 
'uv_factor', 
'uv_rotation', 
]

def inspect_points(t_layer='ACTIVE', t_frame='ACTIVE', t_stroke='SELECT', all_infos=False):
    '''print full points infos of targeted strokes'''
    print('\nPoint infos:')
    for s in strokelist(t_layer=t_layer, t_frame=t_frame, t_stroke=t_stroke):
        if s.select:
            # print(l.info)
            if all_infos:
                for at in s_attrs:
                    print(f' {at} : {getattr(s, at)}')
            for i, p in enumerate(s.points):
                if p.select:
                    print(f'  [{i}]')
                    for pat in p_attrs:
                        print(f'   {pat} : {getattr(p, pat)}') 

def inspect_strokes(t_layer='ACTIVE', t_frame='ACTIVE', t_stroke='SELECT', all_infos=False):
    '''print full points infos of targeted strokes'''
    print('\nStrokes infos:')
    for s in strokelist(t_layer=t_layer, t_frame=t_frame, t_stroke=t_stroke):
        if s.select:
            # print(l.info)
            for at in s_attrs:
                if not hasattr(s, at):
                    continue  
                print(f'  {at} : {getattr(s, at)}')
            print(f'   points : {len(s.points)}')
            print(f'   length : {get_stroke_length(s)}')

def thin_stroke_tips(tip_len=5, middle=0, t_layer='ACTIVE', t_frame='ACTIVE', t_stroke='SELECT'):
    '''Thin tips of strokes on target layers/frames/strokes defaut (active layer > active frame > selected strokes)'''
    for l in get_layers(target=t_layer):
        for f in get_frames(l, target=t_frame):
            for s in get_strokes(f, target=t_stroke):
                abs_thinner_tip(s, tip_len=5, middle=0)

def thin_stroke_tips_percentage(tip_len=30, variance=0, t_layer='ALL', t_frame='ACTIVE', t_stroke='SELECT'):
    '''Thin tips of strokes on target layers/frames/strokes defaut (active layer > active frame > selected strokes)'''
    for s in strokelist(t_layer=t_layer, t_frame=t_frame, t_stroke=t_stroke):
        reshape_rel_thinner_tip_percentage(s, tip_len=tip_len, variance=variance)

## -- Trim / Progressive erase

def trim_tip_point(context, endpoint=True):
    '''endpoint : delete last point, else first point'''
    pref = context.scene.gprsettings
    L, F, S = get_tgts(context)
    ### Last
    # can just filter by task
    if context.mode == 'PAINT_GPENCIL' and pref.use_context:
        layer = bpy.context.object.data.layers.active
        if not layer or not layer.active_frame or not len(layer.active_frame.strokes):
            return
        
        last = layer.active_frame.strokes[get_last_index(context)]#-1 (0 with draw on back is on)
        if len(last.points) > 2:# erase point
            if endpoint:
                last.points.pop(index=-1)#pop default
            else:
                last.points.pop(index=0)
        else:# erase line
            for _ in range( len(last.points) ):
                last.points.pop()
            layer.active_frame.strokes.remove(last)
        return

    ### filters
    for l in get_layers(target=L):
        for f in get_frames(l, target=F):
            for s in get_strokes(f, target=S):
                if len(s.points) > 2:# erase point
                    if endpoint:
                        s.points.pop(index=-1)# pop last default
                    else:
                        s.points.pop(index=0)
                else:# erase line
                    for i in range( len(s.points) ):
                        s.points.pop()
                    f.strokes.remove(s)

#TODO - preserve tip triming (option or another func), (need a "detect fade" function to give at with index the point really start to fade and offset that) 

def delete_stroke(strokes, s):
    for i in range(len(s.points)):
        s.points.pop()#pop all point to update viewport
    strokes.remove(s)

def backup_point_as_dic(p):
    '''backup point as dic (same layer, no parent handling)'''
    attrlist = ['co', 'pressure', 'select', 'strength', 'uv_factor', 'uv_rotation']
    pdic = {}
    for attr in attrlist:
        # pdic = getattr(p, attr)
        pdic[attr] = getattr(p, attr)
    return pdic

def backup_stroke(s, ids=None):
    '''backup given points index if ids pass'''
    stroke_attr_list = ('display_mode', 'draw_cyclic', 'end_cap_mode', 'gradient_factor', 'gradient_shape', 'groups', 'is_nofill_stroke', 'line_width', 'material_index', 'start_cap_mode' )#
    sdic = {}
    for att in stroke_attr_list:
        if hasattr(s, att):
            sdic[att] = getattr(s, att)
    points = []
    if ids:
        for pid in ids:
            points.append(backup_point_as_dic(s.points[pid]))
    else:
        for p in s.points:
            points.append(backup_point_as_dic(p))
    sdic['points'] = points
    return sdic

def pseudo_subdiv(a, b, c, d):
    A = location_to_region(a['co'])
    B = location_to_region(b['co'])
    C = location_to_region(c['co'])
    D = location_to_region(d['co'])

    ABl = vector_len_from_coord(A, B)
    CDl = vector_len_from_coord(C, D)
    average_sampling_dist = mean(ABl, CDl)#in automatic mode should respect this average distance.

    #determine where prolonged vector AB-> cross prolonged vector CD-> (problem : if bad angle...)
    # lets subdivide two last stroke instead.


def to_straight_line(s, keep_points=True, influence=100, straight_pressure=True):
    '''
    keep points : if false only start and end point stay delete all other
    straight_pressure : take the mean pressure of all points and apply to stroke.
    '''
    
    p_len = len(s.points)
    if p_len <= 2: # 1 or 2 points only, cancel
        return

    if straight_pressure:
        mean_pressure = mean([p.pressure for p in s.points])#can use a foreach_get but might not be faster.

    if not keep_points:
        for i in range(p_len-2):
            s.points.pop(index=1)
        if straight_pressure:
            for p in s.points:
                p.pressure = mean_pressure

    else:
        A = s.points[0].co
        B = s.points[-1].co
        # ab_dist = vector_len_from_coord(A,B)
        full_dist = get_stroke_length(s)
        dist_from_start = 0.0
        coord_list = []
        
        for i in range(1, p_len-1):# all but first and last
            dist_from_start += vector_len_from_coord(s.points[i-1],s.points[i])
            ratio = dist_from_start / full_dist
            # dont apply directly (change line as we measure it in loop)
            coord_list.append( point_from_dist_in_segment_3d(A, B, ratio) )
        
        # apply change
        for i in range(1, p_len-1):
            #s.points[i].co = coord_list[i-1]#direct super straight 100%
            s.points[i].co = point_from_dist_in_segment_3d(s.points[i].co, coord_list[i-1], influence / 100)

        if straight_pressure:
            # influenced pressure
            for p in s.points:
                p.pressure = p.pressure + ((mean_pressure - p.pressure) * (influence / 100))


#without reduce (may be faster)
def gp_select_by_angle(tol, invert=False):
    #print(strokelist(t_layer=t_layer, t_frame=t_frame, t_stroke=t_stroke))
    for s in selected_strokes():
        pnum = len(s.points)
        if pnum >= 3:#need at least 3 points to calculate angle
            for i in range(pnum-2):#skip two last -2
                a = location_to_region(s.points[i].co)
                b = location_to_region(s.points[i+1].co)
                c = location_to_region(s.points[i+2].co)
                ab = b-a
                bc = c-b
                
                #test if fasted with numpy than built in angle method !!
                angle = get_angle(ab,bc)
                # direct_angle = degrees(ab.angle(bc))#angle_signed
                # if abs(angle) > tol:
                s.points[i+1].select = (abs(angle) > tol) ^ invert

def gp_select_by_angle_reducted(tol, invert=False):
    #print(strokelist(t_layer=t_layer, t_frame=t_frame, t_stroke=t_stroke))
    for s in selected_strokes():
        keys = []
        pnum = len(s.points)
        if pnum >= 3:#need at least 3 points to calculate angle
            suite = []
            for i in range(pnum-2):#skip two last -2
                a = location_to_region(s.points[i].co)
                b = location_to_region(s.points[i+1].co)
                c = location_to_region(s.points[i+2].co)
                ab = b-a
                bc = c-b
                
                angle = get_angle(ab,bc)#test if fasted with numpy than built in angle method !
                # direct_angle = degrees(ab.angle(bc))#angle_signed
                absangle = abs(angle)

                if absangle > tol:
                    suite.append([i+1, absangle])
                else:
                    if suite:#suite has ended
                        #first element of decreasing filtered list, then index of the points
                        keys.append(sorted(suite, key=lambda x: x[1], reverse=True)[0][0])
                        suite = []
                
            sel_list = [(i in keys) ^ invert for i in range(pnum)]
            s.points.foreach_set('select', sel_list)
            # s.points[i+1].select = abs(angle) > tol
                    
                #calculate vector from current and next and store only "key" points:


### straight by slice and slices getters for polygonize

def straight_stroke_slice(s, influence=100, slices=[], reduce=False, delete=False):
    if not slices:
        slices = [0, len(s.points)]

    if delete:# remove points within slices range (influence is irelevant)
        
        if reduce and isinstance(slices[-1], list) and slices[-1][0]+1 < slices[-1][1]:
            # with reduce on, delete mode often delete last point... substract last slice by one if possible and if reduce is passed
            slices[-1][1] = slices[-1][1] - 1

        for sl in reversed(slices):
            # print(sl)
            for pid in reversed(range(sl[0]+1,sl[1])):#sl[1]+1 ?
                s.points.pop(index=pid)
        return

    for sl in slices:
        s_id, e_id = sl[0], sl[1]
        if e_id >= len(s.points):
            # print('len(s.points): ', len(s.points))
            # print('e_id: ', e_id)
            e_id = len(s.points) - 1

        A = s.points[s_id].co
        B = s.points[e_id].co
        # ab_dist = vector_len_from_coord(A,B)
        full_dist = sum( [vector_len_from_coord(s.points[i],s.points[i+1]) for i in range(s_id, e_id)] )
        dist_from_start = 0.0
        coord_list = []
        
        for i in range(s_id+1, e_id):#all but first and last
            dist_from_start += vector_len_from_coord(s.points[i-1],s.points[i])
            ratio = dist_from_start / full_dist
            # dont apply directly (change line as we measure it in loop)
            coord_list.append( point_from_dist_in_segment_3d(A, B, ratio) )
        
        for count, i in enumerate(range(s_id+1, e_id)):#e_id
            #s.points[i].co = coord_list[i-1]#direct super straight 100%
            s.points[i].co = point_from_dist_in_segment_3d(s.points[i].co, coord_list[count], influence / 100)
    
                

def get_points_id_by_reduced_angles(s, tol):
    #print(strokelist(t_layer=t_layer, t_frame=t_frame, t_stroke=t_stroke))
    keys = []
    pnum = len(s.points)
    if pnum >= 3:#need at least 3 points to calculate angle
        suite = []
        for i in range(pnum-2):#skip two last -2
            a = location_to_region(s.points[i].co)
            b = location_to_region(s.points[i+1].co)
            c = location_to_region(s.points[i+2].co)
            ab = b-a
            bc = c-b
            
            angle = get_angle(ab,bc)#test if fasted with numpy than built in angle method !
            # direct_angle = degrees(ab.angle(bc))#angle_signed
            absangle = abs(angle)

            if absangle > tol:
                suite.append([i+1, absangle])
            else:
                if suite:#suite has ended
                    #first element of decreasing filtered list, then index of the points
                    keys.append(sorted(suite, key=lambda x: x[1], reverse=True)[0][0])
                    suite = []
        if len(keys) > 1:
            keys.insert(0, 0)#add first and last
            keys.append(pnum)
            pairs = [[keys[i], keys[i+1]] for i in range(len(keys)-1)]
            return pairs

def get_points_id_by_angles(s, tol, invert=False):
    pnum = len(s.points)
    pairs = []
    prev = False
    added = 0
    if pnum >= 3:#need at least 3 points to calculate angle
        for i in range(pnum-2):#skip two last -2
            a = location_to_region(s.points[i].co)
            b = location_to_region(s.points[i+1].co)
            c = location_to_region(s.points[i+2].co)
            ab = b-a
            bc = c-b
            angle = get_angle(ab,bc)
            # s.points[i+1].select = (abs(angle) > tol) ^ invert
            if not (abs(angle) > tol) ^ invert:#check without not and invert after if needed...
                added +=1
                if not prev:
                    start = i+1
                prev = True
            else:
                if prev:
                    pairs.append([start, i+1])
                    prev = False

        if added > 1:
            return pairs

def gp_polygonize(s, tol, influence=100, reduce=True, delete=False):#, t_layer='ALL', t_frame='ACTIVE', t_stroke='SELECT'
    #print(strokelist(t_layer=t_layer, t_frame=t_frame, t_stroke=t_stroke))
    if reduce:
        pairs = get_points_id_by_reduced_angles(s, tol)
    else:
        pairs = get_points_id_by_angles(s, tol)
    
    # print('pairs: ', pairs)
    if pairs:
        straight_stroke_slice(s, influence, pairs, reduce=reduce, delete=delete)


def guess_join(same_material=True, proximity_tolerance=0.01, start_point_tolerance=6):
    '''
    start_point_tolerance to 0 means only first point is evaluated on last stroke
    proximity_tolerance set the distance under wich points of other lines are "joinable"
    Return error if no points are found close enough.
    '''
    #get last stroke
    last = bpy.context.object.data.layers.active.active_frame.strokes[-1]
    #strokelist(t_layer='ACTIVE', t_frame='ACTIVE', t_stroke='ALL')
    
    # fpt = last.points[0]
    
    #get other strokes of current layer
    found = False
    if same_material:
        pool = [s for s in bpy.context.object.data.layers.active.active_frame.strokes[:-1] if s.material_index == last.material_index]
    else:
        pool = bpy.context.object.data.layers.active.active_frame.strokes[:-1]

    #clamp
    start_point_tolerance = len(last.points)-1 if start_point_tolerance >= len(last.points) else start_point_tolerance
    closes = []
    ct = 0
    for s in pool:
        for pid, p in enumerate(s.points):
            for i in range(1 + start_point_tolerance):
                if checkalign(location_to_region(p.co), location_to_region(last.points[i].co), tol=proximity_tolerance):#2D check #tol=0.01
                    # print(f'{i} > {pid}')
                    ct+=1
                    found = True
                    ### OLD :0 point index, 1 towards end or not (true false), 2 coordinate, 3 point obj, 4 stroke obj, 5 disance from reference point, index of point on last.
                    ### 0 point index, 1 point, 2 stroke, 3 distance from reference point, 4 ref point index 
                    closes.append([pid, p, s, vector_len_from_coord(last.points[i], p) , i])
        
        # if found:#Dont check for another close stroke that might overlap. (maybe change that later)
        #     break
    
    
    if found :
        print(f'{ct} close points found')
        closes.sort(key=lambda x: x[3])#filter to find point that has the closest distance accross athorized points on the last lines.
        closest = closes[0]#list element
        close_stroke = closest[2]#Target stroke
        
        #check if crossed, if it is do an intersection join thing.
        # print('closest: ', closest)

        start_point_index = closest[4]
        # last.points[start_point_index].select = True#Dbg
        start_id = 0
        end_id = len(close_stroke.points)-1

        from_end_tip = True        
        if closest[0] / len(closest[2].points) >= 0.5:#near end
            end_point_index = clamp(closest[0]-1, start_id, end_id)#point before detected point
            
            slist = [i for i in range(0, end_point_index)]
        
        else:#near start
            from_end_tip = False
            end_point_index = clamp(closest[0]+1, start_id, end_id)#point after detected point
            
            slist = [end_id-i for i in range(end_id-end_point_index)]# ex:[9,8,7,4,3,2]
        
        llist = [i for i in range(start_point_index, len(last.points))]

        # close_stroke.points[end_point_index].select = True#Dbg
        # print('len(close_stroke.points): ', len(close_stroke.points))
        # print('len(last.points): ', len(last.points))

        stardic = [backup_point_as_dic(close_stroke.points[i]) for i in slist]
        lastdic = [backup_point_as_dic(last.points[i]) for i in llist]


        # For smoothness sake, place a "subdivided" point between the tww according to point orientation
        # Will only work in persp view, disable.
        subdiv_points = pseudo_subdiv(stardic[-2], stardic[-1], lastdic[0], lastdic[1])
        all_points_dic = stardic + lastdic
        
        ### Create stroke
        
        ns = bpy.context.object.data.layers.active.active_frame.strokes.new()
        for s_attr in ('display_mode', 'draw_cyclic', 'end_cap_mode', 'gradient_factor', 'gradient_shape', 'line_width', 'material_index', 'start_cap_mode' ):
            ## readonly : 'groups', 'is_nofill_stroke',
            if hasattr(ns, s_attr):
                setattr(ns, s_attr, getattr(last,s_attr))#same stroke settings as last stroke

        ## add all points
        ns.points.add(len(all_points_dic))
        # print('all_points_dic: ', all_points_dic)
        for i, pdic in enumerate(all_points_dic):
            # print('pdic: ', pdic)
            for k, v in pdic.items():
                setattr(ns.points[i], k, v)

        ## delete old stroke
        delete_stroke(bpy.context.object.data.layers.active.active_frame.strokes, close_stroke)
        delete_stroke(bpy.context.object.data.layers.active.active_frame.strokes, last)
        
    else:
        return 'No close stroke found to join last.\nTry increasing the tolerance and check if there is no depth offset from your point of view'


# TODO make a function to join the two last strokes (best would be with a sampled interpolated curve between the last and first point... hard)

def delete_last_stroke():
    '''
    Direct delete of last stroke if any
    Might be quicker than ctrl-Z for heavy scenes
    '''
    # last_strokes = get_strokes(get_frames(get_layers('ACTIVE')[0], 'ACTIVE')[0], 'LAST')[0]
    try:
        ss = bpy.context.object.data.layers.active.active_frame.strokes
        if len(ss):
            # ss.remove(ss[-1])#does not refresh the viewport
            delete_stroke(ss, ss[-1])
        else:
            return ('WARNING', 'no stroke to remove')
    except Exception as e:
        print('Error trying to access last stroke :', e)
        return ('ERROR', 'Error, could not access last stroke')



### ---------- 
###  To Circle
### ----------

def circle_2d_closed(coord, r, num_segments):
    '''
    create circle, ref: http://slabode.exofire.net/circle_draw.shtml
    coord: coordinate of circle center (vector 2d)
    r: radius (float)
    num_segments: number of segment to compose circle, prefer multiples of 4 (int)
    return a list of Vectors
    "closed" mean last point is overlapping first
    '''
    cx, cy = coord
    points = []
    theta = 2 * 3.1415926 / num_segments
    c = math.cos(theta) #precalculate the sine and cosine
    s = math.sin(theta)
    x = r # we start at angle = 0
    y = 0
    for i in range(num_segments):
        #bgl.glVertex2f(x + cx, y + cy) # output vertex
        points.append( Vector((x + cx, y + cy)) )
        # apply the rotation matrix
        t = x
        x = c * x - s * y
        y = s * t + c * y
    # append first point also as last
    points.append(points[0])
    return points

def magnet_on_target(src, tgt):
    '''Proximity transfer from a 2d coord list to another'''
    import mathutils
    casted_coord = []
    for sp in src:
        res = sp
        prevdist = 100000
        for i in range(len(tgt)-1):
            pos, percentage = mathutils.geometry.intersect_point_line(sp, tgt[i], tgt[i+1])

            if percentage <= 0:# at head
                pos = tgt[i]
            elif 1 <= percentage:# at tail
                pos = tgt[i+1]

            ## check if distance is shorter than previous
            dist = (pos-sp).length
            if dist < prevdist:
                # dist can be 'nan', in this case does not enter condition, res equal sp
                res = pos
                prevdist = dist
        
        casted_coord.append(res)
    return casted_coord


""" raw func
def to_circle_cast_to_average():
    ob = C.object
    stroke = ob.data.layers.active.active_frame.strokes[-1]
    coords = [location_to_region(ob.matrix_world @ p.co) for p in stroke.points]

    ## Determine center : mean center ? -better fitting- bounding box (equivalent ?)
    # center = Vector(np.median(coords, axis=0))
    center = Vector(np.mean(coords, axis=0))# mean seem to have better placement than median for user

    ## Determine radius (bounding box ? median length ?)
    dist_list = [(center - co).length for co in coords]

    radius = np.mean(dist_list)
    # radius = np.median(dist_list)

    circle = circle_2d_closed(center, radius, 128)#64

    cast_coords = magnet_on_target(coords, circle)
    for p, nco in zip(stroke.points, cast_coords):
        p.co = ob.matrix_world.inverted() @ region_to_location(nco, p.co)# depth at p.co no good... need reproject """

def to_circle_cast_to_average(ob, point_list, influence = 100, straight_pressure = False):
    '''Project given points on 2d average points'''

    ## TODO reproject on plane if strokes are found coplanar
    ## else reproject on axis given by current blend

    coords = [location_to_region(ob.matrix_world @ p.co) for p in point_list]

    ## Determine center : mean center ? -better fitting- bounding box (equivalent ?)
    # center = Vector(np.median(coords, axis=0))
    center = Vector(np.mean(coords, axis=0))# mean seem to have better placement than median for user

    ## Determine radius (bounding box ? median length ?)
    dist_list = [(center - co).length for co in coords]

    radius = np.mean(dist_list)
    # radius = np.median(dist_list)

    circle = circle_2d_closed(center, radius, 128)#64

    cast_coords = magnet_on_target(coords, circle)
    for p, nco in zip(point_list, cast_coords):
        ## /!\ depth at old point coordinate, jaggy depth... need custom reproject (or warn user to reproject) ?
        new_co3d = ob.matrix_world.inverted() @ region_to_location(nco, p.co)
        p.co = point_from_dist_in_segment_3d(p.co, new_co3d, influence / 100)
    
    if straight_pressure:
        m_pressure = np.median([p.pressure for p in point_list])
        # m_pressure = np.mean([p.pressure for p in point_list])
        for p in point_list:
            # add a percentage of the difference
            p.pressure = p.pressure + ((m_pressure - p.pressure) * (influence / 100))
            # p.pressure = m_pressure #without influence

def is_coplanar_stroke(s, tol=0.0002, verbose=False) -> bool:
    '''
    Get a GP stroke object and tell if all points are coplanar (with a tolerance).
    '''

    if len(s.points) < 4:
        # less than 4 points is necessarily coplanar
        return True 

    obj = bpy.context.object
    mat = obj.matrix_world
    pct = len(s.points)
    a = mat @ s.points[0].co
    b = mat @ s.points[pct//3].co
    c = mat @ s.points[pct//3*2].co

    ab = b-a
    ac = c-a

    # get normal (perpendicular Vector)
    plane_no = ab.cross(ac)#.normalized()

    for i, p in enumerate(s.points):
        ## let a tolerance value of at least 0.0002
        # if abs(geometry.distance_point_to_plane(p.co, a, plane_no)) > tol:
        if abs(geometry.distance_point_to_plane(mat @ p.co, a, plane_no)) > tol:
            if verbose:
                print(f'point{i} is not co-planar') # (distance to plane {geometry.distance_point_to_plane(p.co, a, plane_no)})
            return False
    return True

def get_coplanar_stroke_vector(s, tol=0.0002, verbose=False):
    '''
    Get a GP stroke object and tell if all points are coplanar (with a tolerance).
    return normal vector if coplanar else None
    '''

    if len(s.points) < 4:
        # less than 4 points is necessarily coplanar
        # but not "evaluable" so return None
        if verbose:
            print('less than 4 points')
        return

    obj = bpy.context.object
    mat = obj.matrix_world
    pct = len(s.points)
    a = mat @ s.points[0].co
    b = mat @ s.points[pct//3].co
    c = mat @ s.points[pct//3*2].co

    """
    a = s.points[0].co
    b = s.points[1].co
    c = s.points[-2].co
    """
    ab = b-a
    ac = c-a

    #get normal (perpendicular Vector)
    plane_no = ab.cross(ac)#.normalized()
    val = plane_no

    # print('plane_no: ', plane_no)
    for i, p in enumerate(s.points):
        ## let a tolerance value of at least 0.0002 maybe more
        # if abs(geometry.distance_point_to_plane(p.co, a, plane_no)) > tol:
        if abs(geometry.distance_point_to_plane(mat @ p.co, a, plane_no)) > tol:
            if verbose:
                print(f'point{i} is not co-planar') # (distance to plane {geometry.distance_point_to_plane(p.co, a, plane_no)})
            return
            # val = None
    return val
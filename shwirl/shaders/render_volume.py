from __future__ import division

# This file implements a RenderVolumeVisual class. It is derived from the
# VolumeVisual class in vispy.visuals.volume, which is released under a BSD
# license included here:
#
# ===========================================================================
# Vispy is licensed under the terms of the (new) BSD license:
#
# Copyright (c) 2015, authors of Vispy
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
# * Neither the name of Vispy Development Team nor the names of its
#   contributors may be used to endorse or promote products
#   derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
# IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER
# OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# ===========================================================================
#
# This modified version is released under the (new) BSD license:
#
#   Copyright (c) 2015, Dany Vohl
#   All rights reserved.
#
# A copy of the license is available in the root directory of this project.
#

from shwirl.extern.vispy.gloo import Texture3D, TextureEmulated3D, VertexBuffer, IndexBuffer
from shwirl.extern.vispy.visuals import Visual
from shwirl.extern.vispy.visuals.shaders import Function
from shwirl.extern.vispy.color import get_colormap
from shwirl.extern.vispy.scene.visuals import create_visual_node
from shwirl.extern.vispy.io import load_spatial_filters

import numpy as np

# Vertex shader
VERT_SHADER = """
attribute vec3 a_position;
// attribute vec3 a_texcoord;
uniform vec3 u_shape;

// varying vec3 v_texcoord;
varying vec3 v_position;
varying vec4 v_nearpos;
varying vec4 v_farpos;

void main() {
    // v_texcoord = a_texcoord;
    v_position = a_position;

    // Project local vertex coordinate to camera position. Then do a step
    // backward (in cam coords) and project back. Voila, we get our ray vector.
    vec4 pos_in_cam = $viewtransformf(vec4(v_position, 1));

    // intersection of ray and near clipping plane (z = -1 in clip coords)
    pos_in_cam.z = -pos_in_cam.w;
    v_nearpos = $viewtransformi(pos_in_cam);

    // intersection of ray and far clipping plane (z = +1 in clip coords)
    pos_in_cam.z = pos_in_cam.w;
    v_farpos = $viewtransformi(pos_in_cam);

    gl_Position = $transform(vec4(v_position, 1.0));
}
"""  # noqa

# Fragment shader
FRAG_SHADER = """
// uniforms
uniform $sampler_type u_volumetex;
uniform vec3 u_shape;
uniform vec3 u_resolution;
uniform float u_threshold;
uniform float u_relative_step_size;
//uniform int u_color_scale;
//uniform float u_data_min;
//uniform float u_data_max;

// Moving box filter variables
uniform int u_filter_size;
uniform float u_filter_coeff;
uniform int u_filter_arm;
uniform int u_filter_type;

uniform int u_use_gaussian_filter;
uniform int u_gaussian_filter_size;

//uniform int u_log_scale;

// Volume Stats
//uniform float u_volume_mean;
//uniform float u_volume_std;
//uniform float u_volume_madfm;
uniform float u_high_discard_filter_value;
uniform float u_low_discard_filter_value;
uniform float u_density_factor;

uniform int u_color_method;

//varyings
// varying vec3 v_texcoord;
varying vec3 v_position;
varying vec4 v_nearpos;
varying vec4 v_farpos;

// uniforms for lighting. Hard coded until we figure out how to do lights
const vec4 u_ambient = vec4(0.2, 0.4, 0.2, 1.0);
const vec4 u_diffuse = vec4(0.8, 0.2, 0.2, 1.0);
const vec4 u_specular = vec4(1.0, 1.0, 1.0, 1.0);
const float u_shininess = 40.0;

//varying vec3 lightDirs[1];

// global holding view direction in local coordinates
vec3 view_ray;

float rand(vec2 co)
{{
    // Create a pseudo-random number between 0 and 1.
    // http://stackoverflow.com/questions/4200224
    return fract(sin(dot(co.xy ,vec2(12.9898, 78.233))) * 43758.5453);
}}

float colorToVal(vec4 color1)
{{
    return color1.g;
}}

vec4 movingAverageFilter_line_of_sight(vec3 loc, vec3 step)
{{
    // Initialise variables
    vec4 partial_color = vec4(0.0, 0.0, 0.0, 0.0);

    for ( int i=1; i<=u_filter_arm; i++ )
    {{
        partial_color += $sample(u_volumetex, loc-i*step);
        partial_color += $sample(u_volumetex, loc+i*step);
    }}

    partial_color += $sample(u_volumetex, loc);

    // Evaluate mean
    partial_color *= u_filter_coeff;

    return partial_color;
}}

vec4 Gaussian_5(vec4 color_original, vec3 loc, vec3 direction) {{
  vec4 color = vec4(0.0);
  vec3 off1 = 1.3333333333333333 * direction;
  color += color_original * 0.29411764705882354;
  color += $sample(u_volumetex, loc + (off1 * u_resolution)) * 0.35294117647058826;
  color += $sample(u_volumetex, loc - (off1 * u_resolution)) * 0.35294117647058826;
  return color;
}}

vec4 Gaussian_9(vec4 color_original, vec3 loc, vec3 direction)
{{
    vec4 color = vec4(0.0);
    vec3 off1 = 1.3846153846 * direction;
    vec3 off2 = 3.2307692308 * direction;
    color += color_original * 0.2270270270;
    color += $sample(u_volumetex, loc + (off1 * u_resolution)) * 0.3162162162;
    color += $sample(u_volumetex, loc - (off1 * u_resolution)) * 0.3162162162;
    color += $sample(u_volumetex, loc + (off2 * u_resolution)) * 0.0702702703;
    color += $sample(u_volumetex, loc - (off2 * u_resolution)) * 0.0702702703;
    return color;
}}

vec4 Gaussian_13(vec4 color_original, vec3 loc, vec3 direction) {{
  vec4 color = vec4(0.0);
  vec3 off1 = 1.411764705882353 * direction;
  vec3 off2 = 3.2941176470588234 * direction;
  vec3 off3 = 5.176470588235294 * direction;
  color += color_original * 0.1964825501511404;
  color += $sample(u_volumetex, loc + (off1 * u_resolution)) * 0.2969069646728344;
  color += $sample(u_volumetex, loc - (off1 * u_resolution)) * 0.2969069646728344;
  color += $sample(u_volumetex, loc + (off2 * u_resolution)) * 0.09447039785044732;
  color += $sample(u_volumetex, loc - (off2 * u_resolution)) * 0.09447039785044732;
  color += $sample(u_volumetex, loc + (off3 * u_resolution)) * 0.010381362401148057;
  color += $sample(u_volumetex, loc - (off3 * u_resolution)) * 0.010381362401148057;
  return color;
}}

// ----------------------------------------------------------------
// ----------------------------------------------------------------
// Edge detection Pass
// (adapted from https://www.shadertoy.com/view/MscSzf#)
// ----------------------------------------------------------------
float checkSame(vec4 center, vec4 sample, vec3 resolution) {{
    vec2 centerNormal = center.xy;
    float centerDepth = center.z;
    vec2 sampleNormal = sample.xy;
    float sampleDepth = sample.z;

    vec2 sensitivity = (vec2(0.3, 1.5) * resolution.y / 50.0);

    vec2 diffNormal = abs(centerNormal - sampleNormal) * sensitivity.x;
    bool isSameNormal = (diffNormal.x + diffNormal.y) < 0.1;
    float diffDepth = abs(centerDepth - sampleDepth) * sensitivity.y;
    bool isSameDepth = diffDepth < 0.1;

    return (isSameNormal && isSameDepth) ? 1.0 : 0.0;
}}

vec4 edge_detection(vec4 color_original, vec3 loc, vec3 step, vec3 resolution) {{

    vec4 sample1 = $sample(u_volumetex, loc + (vec3(1., 1., 0.) / resolution));
    vec4 sample2 = $sample(u_volumetex, loc + (vec3(-1., -1., 0.) / resolution));
    vec4 sample3 = $sample(u_volumetex, loc + (vec3(-1., 1., 0.) / resolution));
    vec4 sample4 = $sample(u_volumetex, loc + (vec3(1., -1., 0.) / resolution));

    float edge = checkSame(sample1, sample2, resolution) *
                 checkSame(sample3, sample4, resolution);

    return vec4(color_original.rgb, 1-edge);
}}
// ----------------------------------------------------------------
// ----------------------------------------------------------------

// Used with iso surface
vec4 calculateColor(vec4 betterColor, vec3 loc, vec3 step)
{{
    // Calculate color by incorporating lighting
    vec4 color1;
    vec4 color2;

    // View direction
    vec3 V = normalize(view_ray);

    // calculate normal vector from gradient
    vec3 N; // normal
    color1 = $sample( u_volumetex, loc+vec3(-step[0],0.0,0.0) );
    color2 = $sample( u_volumetex, loc+vec3(step[0],0.0,0.0) );
    N[0] = colorToVal(color1) - colorToVal(color2);
    betterColor = max(max(color1, color2),betterColor);
    color1 = $sample( u_volumetex, loc+vec3(0.0,-step[1],0.0) );
    color2 = $sample( u_volumetex, loc+vec3(0.0,step[1],0.0) );
    N[1] = colorToVal(color1) - colorToVal(color2);
    betterColor = max(max(color1, color2),betterColor);
    color1 = $sample( u_volumetex, loc+vec3(0.0,0.0,-step[2]) );
    color2 = $sample( u_volumetex, loc+vec3(0.0,0.0,step[2]) );
    N[2] = colorToVal(color1) - colorToVal(color2);
    betterColor = max(max(color1, color2),betterColor);
    float gm = length(N); // gradient magnitude
    N = normalize(N);

    // Flip normal so it points towards viewer
    float Nselect = float(dot(N,V) > 0.0);
    N = (2.0*Nselect - 1.0) * N;  // ==  Nselect * N - (1.0-Nselect)*N;

    // Get color of the texture (albeido)
    color1 = betterColor;
    color2 = color1;
    // todo: parametrise color1_to_color2

    // Init colors
    vec4 ambient_color = vec4(0.0, 0.0, 0.0, 0.0);
    vec4 diffuse_color = vec4(0.0, 0.0, 0.0, 0.0);
    vec4 specular_color = vec4(0.0, 0.0, 0.0, 0.0);
    vec4 final_color;

    // todo: allow multiple light, define lights on viewvox or subscene
    int nlights = 1;
    for (int i=0; i<nlights; i++)
    {{
        // Get light direction (make sure to prevent zero devision)
        vec3 L = normalize(view_ray);  //lightDirs[i];
        float lightEnabled = float( length(L) > 0.0 );
        L = normalize(L+(1.0-lightEnabled));

        // Calculate lighting properties
        float lambertTerm = clamp( dot(N,L), 0.0, 1.0 );
        vec3 H = normalize(L+V); // Halfway vector
        float specularTerm = pow( max(dot(H,N),0.0), u_shininess);

        // Calculate mask
        float mask1 = lightEnabled;

        // Calculate colors
        ambient_color +=  mask1 * u_ambient;  // * gl_LightSource[i].ambient;
        diffuse_color +=  mask1 * lambertTerm;
        specular_color += mask1 * specularTerm * u_specular;
    }}

    // Calculate final color by componing different components
    final_color = color2 * ( ambient_color + diffuse_color) + specular_color;
    final_color.a = color2.a;

    // Done
    return final_color;
}}

// for some reason, this has to be the last function in order for the
// filters to be inserted in the correct place...

void main() {{
    vec3 farpos = v_farpos.xyz / v_farpos.w;
    vec3 nearpos = v_nearpos.xyz / v_nearpos.w;

    // Calculate unit vector pointing in the view direction through this
    // fragment.
    view_ray = normalize(farpos.xyz - nearpos.xyz);

    // Compute the distance to the front surface or near clipping plane
    float distance = dot(nearpos-v_position, view_ray);
    distance = max(distance, min((-0.5 - v_position.x) / view_ray.x,
                            (u_shape.x - 0.5 - v_position.x) / view_ray.x));
    distance = max(distance, min((-0.5 - v_position.y) / view_ray.y,
                            (u_shape.y - 0.5 - v_position.y) / view_ray.y));
    distance = max(distance, min((-0.5 - v_position.z) / view_ray.z,
                            (u_shape.z - 0.5 - v_position.z) / view_ray.z));

    // Now we have the starting position on the front surface
    vec3 front = v_position + view_ray * distance;

    // Decide how many steps to take
    int nsteps = int(-distance / u_relative_step_size + 0.5);
    if( nsteps < 1 )
        discard;

    // Get starting location and step vector in texture coordinates
    vec3 step = ((v_position - front) / u_shape) / nsteps;
    vec3 start_loc = front / u_shape;

    // For testing: show the number of steps. This helps to establish
    // whether the rays are correctly oriented
    //gl_FragColor = vec4(0.0, nsteps / 3.0 / u_shape.x, 1.0, 1.0);
    //return;

    {before_loop}

    vec3 loc = start_loc;
    int iter = 0;


    float discard_ratio = 1.0 / (u_high_discard_filter_value - u_low_discard_filter_value);
    float low_discard_ratio = 1.0 / u_low_discard_filter_value;


    for (iter=0; iter<nsteps; iter++)
    {{
        // Get sample color
        vec4 color;

        if (u_filter_size == 1)
            color = $sample(u_volumetex, loc);
        else {{
            color = movingAverageFilter_line_of_sight(loc, step);
        }}

        if (u_use_gaussian_filter==1) {{
            vec4 temp_color;
            vec3 direction;
            if (u_gaussian_filter_size == 5){{
                // horizontal
                direction = vec3(1., 0., 0.);
                temp_color = Gaussian_5(color, loc, direction);

                // vertical
                direction = vec3(0., 1., 0.);
                temp_color = Gaussian_5(temp_color, loc, direction);

                // depth
                direction = vec3(0., 0., 1.);
                temp_color = Gaussian_5(temp_color, loc, direction);
            }}

            if (u_gaussian_filter_size == 9){{
                // horizontal
                direction = vec3(1., 0., 0.);
                temp_color = Gaussian_9(color, loc, direction);

                // vertical
                direction = vec3(0., 1., 0.);
                temp_color = Gaussian_9(temp_color, loc, direction);

                // depth
                direction = vec3(0., 0., 1.);
                temp_color = Gaussian_9(temp_color, loc, direction);
            }}

            if (u_gaussian_filter_size == 13){{
                // horizontal
                direction = vec3(1., 0., 0.);
                temp_color = Gaussian_13(color, loc, direction);

                // vertical
                direction = vec3(0., 1., 0.);
                temp_color = Gaussian_13(temp_color, loc, direction);

                // depth
                direction = vec3(0., 0., 1.);
                temp_color = Gaussian_13(temp_color, loc, direction);
            }}
            color = temp_color;
        }}

        float val = color.g;

        // To force activating the uniform - this should be done differently
        float density_factor = u_density_factor;

        if (u_filter_type == 1) {{
            // Get rid of very strong signal values
            if (val > u_high_discard_filter_value)
            {{
                val = 0.;
            }}

            // Don't consider noisy values
            //if (val < u_volume_mean - 3*u_volume_std)
            if (val < u_low_discard_filter_value)
            {{
                val = 0.;
            }}

            if (u_low_discard_filter_value == u_high_discard_filter_value)
            {{
                if (u_low_discard_filter_value != 0.)
                {{
                    val *= low_discard_ratio;
                }}
            }}
            else {{
                val -= u_low_discard_filter_value;
                val *= discard_ratio;
            }}
        }}
        else {{
            if (val > u_high_discard_filter_value)
            {{
                val = 0.;
            }}

            if (val < u_low_discard_filter_value)
            {{
                val = 0.;
            }}
        }}

        {in_loop}

        // Advance location deeper into the volume
        loc += step;
    }}

    {after_loop}

    //gl_FragColor = edge_detection(gl_FragColor, loc, step, u_shape);

    /* Set depth value - from visvis TODO
    int iter_depth = int(maxi);
    // Calculate end position in world coordinates
    vec4 position2 = vertexPosition;
    position2.xyz += ray*shape*float(iter_depth);
    // Project to device coordinates and set fragment depth
    vec4 iproj = gl_ModelViewProjectionMatrix * position2;
    iproj.z /= iproj.w;
    gl_FragDepth = (iproj.z+1.0)/2.0;
    */
}}


"""  # noqa


MIP_SNIPPETS = dict(
    before_loop="""
        float maxval = -99999.0; // The maximum encountered value
        int maxi = 0;  // Where the maximum value was encountered
        """,
    in_loop="""
        if( val > maxval ) {
            maxval = val;
            maxi = iter;
        }
        """,
    after_loop="""
        // Refine search for max value
        loc = start_loc + step * (float(maxi) - 0.5);

        for (int i=0; i<10; i++) {
            maxval = max(maxval, $sample(u_volumetex, loc).g);
            loc += step * 0.1;
        }

        if (maxval > u_high_discard_filter_value || maxval < u_low_discard_filter_value)
        {{
            maxval = 0.;
        }}

        // Color is associated to voxel intensity
        if (u_color_method == 0) {
            gl_FragColor = $cmap(maxval);
            //gl_FragColor.a = maxval;
        }
        else{
            // Color is associated to redshift/velocity
            if (u_color_method == 1) {
                gl_FragColor = $cmap(loc.y);

                //if (maxval == 0)
                    gl_FragColor.a = maxval;
            }
            // Color is associated to RGB cube
            else {
                if (u_color_method == 2) {
                    gl_FragColor.r = loc.y;
                    gl_FragColor.g = loc.z;
                    gl_FragColor.b = loc.x;
                    gl_FragColor.a = maxval;
                }
                // Case 4: Mom2
                // TODO: verify implementation of MIP-mom2.
                else {
                   gl_FragColor = $cmap((maxval * ((maxval - loc.y) * (maxval - loc.y))) / maxval);
                }
            }
        }

        """,
)
MIP_FRAG_SHADER = FRAG_SHADER.format(**MIP_SNIPPETS)


LMIP_SNIPPETS = dict(
    before_loop="""
        float maxval = -99999.0; // The maximum encountered value
        float local_maxval = -99999.0; // The local maximum encountered value
        int maxi = 0;  // Where the maximum value was encountered
        int local_maxi = 0;  // Where the local maximum value was encountered
        bool local_max_found = false;
        """,
    in_loop="""
        if( val > u_threshold && !local_max_found ) {
            local_maxval = val;
            local_maxi = iter;
            local_max_found = true;
        }

        if( val > maxval) {
            maxval = val;
            maxi = iter;
        }
        """,
    after_loop="""
        if (!local_max_found) {
            local_maxval = maxval;
            local_maxi = maxi;
        }

        // Refine search for max value
        loc = start_loc + step * (float(local_maxi) - 0.5);
        for (int i=0; i<10; i++) {
            local_maxval = max(local_maxval, $sample(u_volumetex, loc).g);
            loc += step * 0.1;
        }

        if (local_maxval > u_high_discard_filter_value) {
            local_maxval = 0.;
        }

        if (local_maxval < u_low_discard_filter_value) {
            local_maxval = 0.;
        }

        // Color is associated to voxel intensity
        if (u_color_method == 0) {
            gl_FragColor = $cmap(local_maxval);
            gl_FragColor.a = local_maxval;
        }
        // Color is associated to redshift/velocity
        else {
            gl_FragColor = $cmap(loc.y);
            gl_FragColor.a = local_maxval;
        }
        """,
)
LMIP_FRAG_SHADER = FRAG_SHADER.format(**LMIP_SNIPPETS)


TRANSLUCENT_SNIPPETS = dict(
    before_loop="""
        vec4 integrated_color = vec4(0., 0., 0., 0.);
        float mom0 = 0.;
        float mom1 = 0.;
        float ratio = 1/nsteps; // final average
        float a1 = 0.;
        float a2 = 0.;
        """,
    in_loop="""
            float alpha;
            // Case 1: Color is associated to voxel intensity
            if (u_color_method == 0) {
                /*color = $cmap(val);
                a1 = integrated_color.a;
                a2 = val * density_factor * (1 - a1);

                alpha = max(a1 + a2, 0.001);

                integrated_color *= a1 / alpha;
                integrated_color += color * a2 / alpha;*/

                color = $cmap(val);

                a1 = integrated_color.a;
                a2 = val * density_factor * (1 - a1);

                alpha = max(a1 + a2, 0.001);

                integrated_color *= a1 / alpha;
                integrated_color += color * a2 / alpha;

            }
            else{
                // Case 2: Color is associated to redshift/velocity
                if (u_color_method == 1) {
                    color = $cmap(loc.y);
                    a1 = integrated_color.a;
                    a2 = val * density_factor * (1 - a1);

                    alpha = max(a1 + a2, 0.001);

                    integrated_color *= a1 / alpha;
                    integrated_color.rgb += color.rgb * a2 / alpha;
                }
                // Case 3: Color is associated to RGB cube
                else {
                    if (u_color_method == 2){
                        color.r = loc.y;
                        color.g = loc.z;
                        color.b = loc.x;
                        a1 = integrated_color.a;
                        a2 = val * density_factor * (1 - a1);

                        alpha = max(a1 + a2, 0.001);

                        integrated_color *= a1 / alpha;
                        integrated_color.rgb += color.rgb * a2 / alpha;
                    }
                    // Case 4: Mom2
                    // TODO: Finish implementation of mom2 (not correct in its present form).
                    else {
                        // mom0
                        a1 = mom0;
                        a2 = val * density_factor * (1 - a1);

                        alpha = max(a1 + a2, 0.001);

                        mom0 *= a1 / alpha;
                        mom0 += val * a2 / alpha;

                        // mom1
                        a1 = mom1;
                        a2 = val * density_factor * (1 - a1);

                        alpha = max(a1 + a2, 0.001);

                        mom1 *= a1 / alpha;
                        mom1 += loc.y * a2 / alpha;
                    }
                }
            }

            integrated_color.a = alpha;

            // stop integrating if the fragment becomes opaque
            if( alpha > 0.99 ){
                iter = nsteps;
            }

        """,
    after_loop="""

        if (u_color_method != 3){
            gl_FragColor = integrated_color;
        }
        else {
            gl_FragColor = $cmap((mom0  * (mom0-mom1 * mom0-mom1)) / mom0);
        }
        """,
)
TRANSLUCENT_FRAG_SHADER = FRAG_SHADER.format(**TRANSLUCENT_SNIPPETS)

TRANSLUCENT2_SNIPPETS = dict(
    before_loop="""
        vec4 integrated_color = vec4(0., 0., 0., 0.);
        float ratio = 1/nsteps; // final average
        """,
    in_loop="""
            float alpha;
            // Case 1: Color is associated to voxel intensity
            if (u_color_method == 0) {
                color = $cmap(val);
                integrated_color = (val * density_factor + integrated_color.a * (1 - density_factor)) * color;
                alpha = integrated_color.a;

                //alpha = a1+a2;
                // integrated_color *= a1 / alpha;
                // integrated_color += color * a2 / alpha;
            }
            else{
                // Case 2: Color is associated to redshift/velocity
                if (u_color_method == 1) {
                    color = $cmap(loc.y);
                    float a1 = integrated_color.a;
                    float a2 = val * density_factor * (1 - a1);

                    alpha = max(a1 + a2, 0.001);

                    integrated_color *= a1 / alpha;
                    integrated_color.rgb += color.rgb * a2 / alpha;
                }
                // Case 3: Color is associated to RGB cube
                else {
                    color.r = loc.x;
                    color.g = loc.z;
                    color.b = loc.y;
                    float a1 = integrated_color.a;
                    float a2 = val * density_factor * (1 - a1);

                    alpha = max(a1 + a2, 0.001);

                    integrated_color *= a1 / alpha;
                    integrated_color.rgb += color.rgb * a2 / alpha;
                }
            }

            integrated_color.a = alpha;

            // stop integrating if the fragment becomes opaque
            if( alpha > 0.99 ){
                iter = nsteps;
            }

        """,
    after_loop="""
        gl_FragColor = integrated_color;
        """,
)
TRANSLUCENT2_FRAG_SHADER = FRAG_SHADER.format(**TRANSLUCENT2_SNIPPETS)



ADDITIVE_SNIPPETS = dict(
    before_loop="""
        vec4 integrated_color = vec4(0., 0., 0., 0.);
        """,
    in_loop="""
        color = $cmap(val);

        integrated_color = 1.0 - (1.0 - integrated_color) * (1.0 - color);
        """,
    after_loop="""
        gl_FragColor = integrated_color;
        """,
)
ADDITIVE_FRAG_SHADER = FRAG_SHADER.format(**ADDITIVE_SNIPPETS)


ISO_SNIPPETS = dict(
    before_loop="""
        vec4 color3 = vec4(0.0);  // final color
        vec3 dstep = 1.5 / u_shape;  // step to sample derivative
        gl_FragColor = vec4(0.0);
    """,
    in_loop="""
        if (val > u_threshold-0.2) {
            // Take the last interval in smaller steps
            vec3 iloc = loc - step;
            for (int i=0; i<10; i++) {
                val = $sample(u_volumetex, iloc).g;
                if (val > u_threshold) {
                    color = $cmap(val);
                    gl_FragColor = calculateColor(color, iloc, dstep);
                    iter = nsteps;
                    break;
                }
                iloc += step * 0.1;
            }
        }
        """,
    after_loop="""
        """,
)

ISO_FRAG_SHADER = FRAG_SHADER.format(**ISO_SNIPPETS)

frag_dict = {
    'mip': MIP_FRAG_SHADER,
    'lmip': LMIP_FRAG_SHADER,
    'iso': ISO_FRAG_SHADER,
    'avip': TRANSLUCENT_FRAG_SHADER,
    'translucent2': TRANSLUCENT2_FRAG_SHADER,
    'additive': ADDITIVE_FRAG_SHADER,
}

# _interpolation_template = """
#     #include "misc/spatial-filters.frag"
#     vec4 texture_lookup_filtered(vec2 texcoord) {
#         if(texcoord.x < 0.0 || texcoord.x > 1.0 ||
#         texcoord.y < 0.0 || texcoord.y > 1.0) {
#             discard;
#         }
#         return %s($texture, $shape, texcoord);
#     }"""
#
# _texture_lookup = """
#     vec4 texture_lookup(vec2 texcoord) {
#         if(texcoord.x < 0.0 || texcoord.x > 1.0 ||
#         texcoord.y < 0.0 || texcoord.y > 1.0) {
#             discard;
#         }
#         return texture2D($texture, texcoord);
#     }"""


class RenderVolumeVisual(Visual):
    """ Displays a 3D Volume
    
    Parameters
    ----------
    vol : ndarray
        The volume to display. Must be ndim==3.
    clim : tuple of two floats | None
        The contrast limits. The values in the volume are mapped to
        black and white corresponding to these values. Default maps
        between min and max.
    method : {'mip', 'avip', 'additive', 'iso'}
        The render method to use. See corresponding docs for details.
        Default 'mip'.
    threshold : float
        The threshold to use for the isosurafce render method. By default
        the mean of the given volume is used.
    relative_step_size : float
        The relative step size to step through the volume. Default 0.8.
        Increase to e.g. 1.5 to increase performance, at the cost of
        quality.
    cmap : str
        Colormap to use.
    emulate_texture : bool
        Use 2D textures to emulate a 3D texture. OpenGL ES 2.0 compatible,
        but has lower performance on desktop platforms.
    """

    def __init__(self, vol, clim=None, method='mip', threshold=None, 
                 relative_step_size=0.8, cmap='grays',
                 emulate_texture=False, color_scale='linear',
                 filter_type = 0, filter_size = 1,
                 use_gaussian_filter = False, gaussian_filter_size=9,
                 density_factor=0.01, color_method='Moment 0', log_scale=0,
                 interpolation='linear'):

        tex_cls = TextureEmulated3D if emulate_texture else Texture3D

        # Storage of information of volume
        self._vol_shape = ()
        self._clim = None
        self._need_vertex_update = True

        # Set the colormap
        self._cmap = get_colormap(cmap)

        # Create gloo objects
        self._vertices = VertexBuffer()
        self._texcoord = VertexBuffer(
            np.array([
                [0, 0, 0],
                [1, 0, 0],
                [0, 1, 0],
                [1, 1, 0],
                [0, 0, 1],
                [1, 0, 1],
                [0, 1, 1],
                [1, 1, 1],
            ], dtype=np.float32))

        # # load 'float packed rgba8' interpolation kernel
        # # to load float interpolation kernel use
        # # `load_spatial_filters(packed=False)`
        # kernel, self._interpolation_names = load_spatial_filters()
        #
        # fun = [Function(_interpolation_template % n)
        #        for n in self._interpolation_names]
        #
        # self._interpolation_names = [n.lower()
        #                              for n in self._interpolation_names]
        #
        # self._interpolation_fun = dict(zip(self._interpolation_names, fun))
        # self._interpolation_names.sort()
        # self._interpolation_names = tuple(self._interpolation_names)
        #
        # print self._interpolation_fun
        #
        # # overwrite "nearest" and "bilinear" spatial-filters
        # # with  "hardware" interpolation _data_lookup_fn
        # self._interpolation_fun['nearest'] = Function(_texture_lookup)
        # self._interpolation_fun['bilinear'] = Function(_texture_lookup)
        #
        # if interpolation not in self._interpolation_names:
        #     raise ValueError("interpolation must be one of %s" %
        #                      ', '.join(self._interpolation_names))
        #
        # self._interpolation = interpolation

        # check texture interpolation
        # if self._interpolation == 'bilinear':
        #     self._interpolation = 'linear'
        # else:
        #     self._interpolation = 'nearest'

        self._tex = tex_cls((10, 10, 10), interpolation=interpolation,
                            wrapping='clamp_to_edge')

        # self._tex = tex_cls((10, 10, 10), interpolation='linear',
        #                     wrapping='clamp_to_edge')

        # Create program
        Visual.__init__(self, vcode=VERT_SHADER, fcode="")
        self.shared_program['u_volumetex'] = self._tex
        self.shared_program['a_position'] = self._vertices
        self.shared_program['a_texcoord'] = self._texcoord
        self._draw_mode = 'triangle_strip'
        self._index_buffer = IndexBuffer()

        # Only show back faces of cuboid. This is required because if we are
        # inside the volume, then the front faces are outside of the clipping
        # box and will not be drawn.
        self.set_gl_state('translucent', cull_face=False)

        # Set data
        self.set_data(vol, clim)

        # Set params
        self.method = method
        self.relative_step_size = relative_step_size
        #self.color_scale = color_scale
        # self.data_min = self._clim[0]
        # self.data_max = self._clim[1]

        # moving_box_filter (=1 means no filter)
        self.filter_type = filter_type
        self.filter_size = filter_size
        # 3D gaussian filter
        self.use_gaussian_filter = use_gaussian_filter
        self.gaussian_filter_size = gaussian_filter_size
        self.log_scale = log_scale
        self.density_factor = density_factor
        self.color_method = color_method

        self.threshold = threshold if (threshold is not None) else vol.mean()
        # print ("threshold", self.threshold)
        self.freeze()

    def set_data(self, vol, clim=None):
        """ Set the volume data.

        Parameters
        ----------
        vol : ndarray
            The 3D volume.
        clim : tuple | None
            Colormap limits to use. None will use the min and max values.
        """
        # Check volume
        if not isinstance(vol, np.ndarray):
            raise ValueError('Volume visual needs a numpy array.')
        if not ((vol.ndim == 3) or (vol.ndim == 4 and vol.shape[-1] <= 4)):
            raise ValueError('Volume visual needs a 3D image.')

        # Handle clim
        if clim is not None:
            clim = np.array(clim, float)
            if not (clim.ndim == 1 and clim.size == 2):
                raise ValueError('clim must be a 2-element array-like')
            self._clim = tuple(clim)
        if self._clim is None:
            self._clim = np.nanmin(vol), np.nanmax(vol)

        # Apply clim
        vol = np.flipud(np.array(vol, dtype='float32', copy=False))
        if self._clim[1] == self._clim[0]:
            if self._clim[0] != 0.:
                vol *= 1.0 / self._clim[0]
        else:
            vol -= self._clim[0]
            vol /= self._clim[1] - self._clim[0]

        # Deal with nan
        if np.isnan(vol).any():
            vol = np.nan_to_num(vol)

        self.high_discard_filter_value = self._clim[1]
        self.low_discard_filter_value = self._clim[0]

        # self.volume_mean = np.mean(vol)
        # self.volume_std = np.std(vol)
        # self.volume_madfm = self.madfm(vol)

        # Apply to texture
        self._tex.set_data(vol)  # will be efficient if vol is same shape
        self.shared_program['u_shape'] = (vol.shape[2], vol.shape[1],
                                          vol.shape[0])

        self.shared_program['u_resolution'] = (1/vol.shape[2], 1/vol.shape[1],
                                          1/vol.shape[0])

        shape = vol.shape[:3]
        if self._vol_shape != shape:
            self._vol_shape = shape
            self._need_vertex_update = True
        self._vol_shape = shape

        # Get some stats
        self._kb_for_texture = np.prod(self._vol_shape) / 1024

    @property
    def interpolation(self):
        """ Current interpolation function.
        """
        return self._tex.interpolation

    @interpolation.setter
    def interpolation(self, interpolation):
        # set interpolation technique
        self._tex.interpolation = interpolation

    @property
    def clim(self):
        """ The contrast limits that were applied to the volume data.
        Settable via set_data().
        """
        return self._clim

    @property
    def cmap(self):
        return self._cmap

    @cmap.setter
    def cmap(self, cmap):
        self._cmap = get_colormap(cmap)
        self.shared_program.frag['cmap'] = Function(self._cmap.glsl_map)
        self.update()

    @property
    def method(self):
        """The render method to use

        Current options are:

            * avip: voxel colors are blended along the view ray until
              the result is opaque.
            * mip: maxiumum intensity projection. Cast a ray and display the
              maximum value that was encountered.
            * additive: voxel colors are added along the view ray until
              the result is saturated.
            * iso: isosurface. Cast a ray until a certain threshold is
              encountered. At that location, lighning calculations are
              performed to give the visual appearance of a surface.
        """
        return self._method

    @method.setter
    def method(self, method):
        # Check and save
        known_methods = list(frag_dict.keys())
        if method not in known_methods:
            raise ValueError('Volume render method should be in %r, not %r' %
                             (known_methods, method))
        self._method = method
        # Get rid of specific variables - they may become invalid
        if 'u_threshold' in self.shared_program:
            self.shared_program['u_threshold'] = None

        self.shared_program.frag = frag_dict[method]
        self.shared_program.frag['sampler_type'] = self._tex.glsl_sampler_type
        self.shared_program.frag['sample'] = self._tex.glsl_sample
        self.shared_program.frag['cmap'] = Function(self._cmap.glsl_map)
        self.update()

    @property
    def color_method(self):
        """The way color is associated with voxel

        Current options are:

            * regular: Color is associated to voxel intensity (defined by the VR method)
            * velocity/redshit: Color is associated to depth coordinate
                                and alpha to voxel intensity (defined by the VR method)
        """
        return self._color_method

    @color_method.setter
    def color_method(self, color_method):
        if color_method == 'Moment 0':
            self._color_method = 0
        elif color_method == 'Moment 1':
            self._color_method = 1
        elif color_method == 'rgb_cube':
            self._color_method = 2
        else:
            self._color_method = 3

        # print ("color_method", self._color_method)
        self.shared_program['u_color_method'] = int(self._color_method)
        self.update()

    @property
    def threshold(self):
        """ The threshold value to apply for the isosurface render method.
            Also used for the lmip transfer function.
        """
        return self._threshold

    @threshold.setter
    def threshold(self, value):
        self._threshold = float(value)

        if 'u_threshold' in self.shared_program:
            self.shared_program['u_threshold'] = self._threshold
        self.update()

    @property
    def color_scale(self):
        return self._color_scale

    @color_scale.setter
    def color_scale(self, color_scale):
        if (color_scale == 'linear'):
            self._color_scale = 0
        else:
            self._color_scale = 1

        self.shared_program['u_color_scale'] = int(self._color_scale)
        self.update()

    @property
    def log_scale(self):
        return self._log_scale

    @log_scale.setter
    def log_scale(self, log_scale):
        self._log_scale = int(log_scale)
        #self.shared_program['u_log_scale'] = int(self._log_scale)
        self.update()

    @property
    def data_min(self):
        return self._data_min

    @data_min.setter
    def data_min(self, data_min):
        self._data_min = 0.

        self.shared_program['u_data_min'] = float(self._data_min)
        self.update()

    @property
    def data_max(self):
        return self._data_max

    @data_max.setter
    def data_max(self, data_max):
        self._data_max = 0.

        self.shared_program['u_data_max'] = float(self._data_max)
        self.update()

    @property
    def moving_box_filter(self):
        return self._moving_box_filter

    @moving_box_filter.setter
    def moving_box_filter(self, moving_box_filter):
        self.shared_program['u_moving_box_filter'] = int(self._moving_box_filter)
        self.update()

    @property
    def volume_mean(self):
        return self._volume_mean

    @volume_mean.setter
    def volume_mean(self, volume_mean):
        self._volume_mean = float(volume_mean)
        # Scale to [0,1]
        self._volume_mean -= self._clim[0]
        self._volume_mean /= self._clim[1] - self._clim[0]
        self.shared_program['u_volume_mean'] = self._volume_mean
        # print ("self._volume_mean", self._volume_mean)
        self.update()

    @property
    def volume_std(self):
        return self._volume_std

    @volume_std.setter
    def volume_std(self, volume_std):
        self._volume_std = float(volume_std)
        self._volume_std -= self._clim[0]
        self._volume_std /= self._clim[1] - self._clim[0]
        self.shared_program['u_volume_std'] = self._volume_std
        self.update()

    @property
    def volume_madfm(self):
        return self._volume_madfm

    @volume_madfm.setter
    def volume_madfm(self, volume_madfm):
        self._volume_madfm = float(volume_madfm)
        self._volume_madfm -= self._clim[0]
        self._volume_madfm /= self._clim[1] - self._clim[0]
        self.shared_program['u_volume_madfm'] = self._volume_madfm
        self.update()

    @property
    def filter_size(self):
        return self._filter_size

    @filter_size.setter
    def filter_size(self, filter_size):
        self._filter_size = int(filter_size)
        self.shared_program['u_filter_size'] = int(self._filter_size)
        self.shared_program['u_filter_arm'] = int(np.floor(self._filter_size/2))
        self.shared_program['u_filter_coeff'] = float(1/self._filter_size)
        self.update()

    @property
    def filter_type(self):
        return self._filter_type

    @filter_type.setter
    def filter_type(self, filter_type):
        if filter_type == 'Rescale':
            self._filter_type = 1
        else:
            self._filter_type = 0

        self.shared_program['u_filter_type'] = int(self._filter_type)
        self.update()

    @property
    def use_gaussian_filter(self):
        return self._use_gaussian_filter

    @use_gaussian_filter.setter
    def use_gaussian_filter(self, use_gaussian_filter):
        # print ("use_gaussian_filter", use_gaussian_filter)
        self._use_gaussian_filter = int(use_gaussian_filter)
        self.shared_program['u_use_gaussian_filter'] = int(self._use_gaussian_filter)
        self.update()

    @property
    def gaussian_filter_size(self):
        return self._gaussian_filter_size

    @gaussian_filter_size.setter
    def gaussian_filter_size(self, gaussian_filter_size):
        self._gaussian_filter_size = int(gaussian_filter_size)
        self.shared_program['u_gaussian_filter_size'] = int(self._gaussian_filter_size)
        self.update()

    @property
    def high_discard_filter_value(self):
        return self._high_discard_filter_value

    @high_discard_filter_value.setter
    def high_discard_filter_value(self, high_discard_filter_value):
        self._high_discard_filter_value = float(high_discard_filter_value)
        self._high_discard_filter_value -= self._clim[0]
        self._high_discard_filter_value /= self._clim[1] - self._clim[0]

        self.shared_program['u_high_discard_filter_value'] = self._high_discard_filter_value

        self.update()

    @property
    def low_discard_filter_value(self):
        return self._low_discard_filter_value

    @low_discard_filter_value.setter
    def low_discard_filter_value(self, low_discard_filter_value):
        self._low_discard_filter_value = float(low_discard_filter_value)
        self._low_discard_filter_value -= self._clim[0]
        self._low_discard_filter_value /= self._clim[1] - self._clim[0]

        self.shared_program['u_low_discard_filter_value'] = self._low_discard_filter_value

        self.update()
        
    @property
    def density_factor(self):
        return self._density_factor

    @density_factor.setter
    def density_factor(self, density_factor):
        self._density_factor = float(density_factor)

        self.shared_program['u_density_factor'] = self._density_factor

        self.update()

    @property
    def relative_step_size(self):
        """ The relative step size used during raycasting.
        
        Larger values yield higher performance at reduced quality. If
        set > 2.0 the ray skips entire voxels. Recommended values are
        between 0.5 and 1.5. The amount of quality degradation depends
        on the render method.
        """
        return self._relative_step_size
    
    @relative_step_size.setter
    def relative_step_size(self, value):
        value = float(value)
        if value < 0.1:
            raise ValueError('relative_step_size cannot be smaller than 0.1')
        self._relative_step_size = value
        self.shared_program['u_relative_step_size'] = value

    def _create_vertex_data(self):
        """ Create and set positions and texture coords from the given shape
        
        We have six faces with 1 quad (2 triangles) each, resulting in
        6*2*3 = 36 vertices in total.
        """
        shape = self._vol_shape
        
        # Get corner coordinates. The -0.5 offset is to center
        # pixels/voxels. This works correctly for anisotropic data.
        x0, x1 = -0.5, shape[2] - 0.5
        y0, y1 = -0.5, shape[1] - 0.5
        z0, z1 = -0.5, shape[0] - 0.5

        pos = np.array([
            [x0, y0, z0],
            [x1, y0, z0],
            [x0, y1, z0],
            [x1, y1, z0],
            [x0, y0, z1],
            [x1, y0, z1],
            [x0, y1, z1],
            [x1, y1, z1],
        ], dtype=np.float32)

        """
          6-------7
         /|      /|
        4-------5 |
        | |     | |
        | 2-----|-3
        |/      |/
        0-------1
        """
        
        # Order is chosen such that normals face outward; front faces will be
        # culled.
        indices = np.array([2, 6, 0, 4, 5, 6, 7, 2, 3, 0, 1, 5, 3, 7],
                           dtype=np.uint32)
        
        # Apply
        self._vertices.set_data(pos)
        self._index_buffer.set_data(indices)

    def _compute_bounds(self, axis, view):
        return 0, self._vol_shape[axis]

    def _prepare_transforms(self, view):
        trs = view.transforms
        view.view_program.vert['transform'] = trs.get_transform()

        view_tr_f = trs.get_transform('visual', 'document')
        view_tr_i = view_tr_f.inverse
        view.view_program.vert['viewtransformf'] = view_tr_f
        view.view_program.vert['viewtransformi'] = view_tr_i

    def _prepare_draw(self, view):
        if self._need_vertex_update:
            self._create_vertex_data()

    def madfm(self, volume):
        # As defined in Whiting, M. T. "DUCHAMP: a 3D source finder for spectral-lines data", MNRAS, 2012.
        return np.median(volume - np.median(volume)) * 1.4826042

RenderVolume = create_visual_node(RenderVolumeVisual)

def get_interpolation_fun():
    return get_interpolation_fun()
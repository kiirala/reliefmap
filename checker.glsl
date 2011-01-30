[VertexShader]
varying vec3 v_V;
varying vec3 v_N;

void main() {
  gl_Position = ftransform();
  v_V = (gl_ModelViewMatrix * gl_Vertex).xyz;
  v_N = gl_NormalMatrix * gl_Normal;
  gl_TexCoord[0] = gl_MultiTexCoord0;
}
[FragmentShader]
varying vec3 v_V;
varying vec3 v_N;

void main() {
  vec3 N = normalize(v_N);
  vec3 V = normalize(v_V);
  vec3 R = reflect(V, N);
  vec3 L = normalize(v_V.xyz - gl_LightSource[0].position.xyz);
  
  vec4 color;
  vec4 scolor;
  float shininess;
  float scale = 16.0;
  if (fract(gl_TexCoord[0].x * scale) >= 0.5 ^^ fract(gl_TexCoord[0].y * scale) >= 0.5) {
    color = vec4(244.0/255.0, 225.0/255.0, 207.0/255.0, 1.0);
    scolor = vec4(color.xyz * 0.25, 1.0);
    shininess = 4.0;
  }
  else {
    color = vec4(32.0/255.0, 49.0/255.0, 66.0/255.0, 1.0);
    scolor = vec4(0.9, 0.9, 0.9, 1.0);
    shininess = 64.0;
  }
  vec4 ambient = vec4(0.2) * color;
  vec4 diffuse = color * max(dot(-L, N), 0.0);
  vec4 specular = scolor * pow(max(dot(R, -L), 0.0), shininess);
  
  gl_FragColor = ambient + diffuse + specular;
}

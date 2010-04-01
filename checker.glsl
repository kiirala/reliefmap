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
	vec3 L = normalize(vec3(gl_LightSource[0].position));

	vec4 color;
	float shininess;
	float scale = 4.0;
	if (fract(gl_TexCoord[0].x * scale) >= 0.5 ^^ fract(gl_TexCoord[0].y * scale) >= 0.5) {
		color = vec4(1.0);
		shininess = 32.0;
	}
	else {
		color = vec4(0.3);
		shininess = 64.0;
	}
	vec4 ambient = vec4(0.2) * color;
	vec4 diffuse = color * max(dot(L, N), 0.0);
	vec4 specular = gl_FrontMaterial.specular * pow(max(dot(R, L), 0.0), shininess);

	gl_FragColor = ambient + diffuse + specular;
}

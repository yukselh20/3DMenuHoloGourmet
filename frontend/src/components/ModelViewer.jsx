import React, { Suspense, useRef, useEffect, useState } from 'react';
import { Canvas, useFrame, useLoader } from '@react-three/fiber';
import { OrbitControls, Environment, PerspectiveCamera, Html } from '@react-three/drei';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';
import * as THREE from 'three';

function Model({ url, dimensions }) {
  const gltf = useLoader(GLTFLoader, url);
  const meshRef = useRef();
  const [modelSize, setModelSize] = useState({ x: 1, y: 1, z: 1 });

  useEffect(() => {
    if (gltf && gltf.scene) {
      // Calculate the bounding box of the model
      const box = new THREE.Box3().setFromObject(gltf.scene);
      const size = new THREE.Vector3();
      box.getSize(size);
      
      setModelSize({ x: size.x, y: size.y, z: size.z });
      
      // Center the model
      const center = new THREE.Vector3();
      box.getCenter(center);
      gltf.scene.position.sub(center);
      
      // Scale the model based on real-world dimensions if provided
      if (dimensions && dimensions.diameter) {
        // Assume the model should fit within the diameter dimension
        const maxDimension = Math.max(size.x, size.z);
        const targetSize = dimensions.diameter / 100; // Convert cm to meters
        const scaleFactor = targetSize / maxDimension;
        gltf.scene.scale.multiplyScalar(scaleFactor);
      }
    }
  }, [gltf, dimensions]);

  useFrame(() => {
    if (meshRef.current) {
      // Subtle rotation animation
      meshRef.current.rotation.y += 0.002;
    }
  });

  return (
    <primitive
      ref={meshRef}
      object={gltf.scene}
      dispose={null}
    />
  );
}

function LoadingFallback() {
  return (
    <Html center>
      <div className="text-white text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-2"></div>
        <p>Loading 3D model...</p>
      </div>
    </Html>
  );
}

const ModelViewer = ({ modelUrl, dimensions, className = '' }) => {
  return (
    <div className={`w-full h-full ${className}`} data-testid="model-viewer">
      <Canvas
        shadows
        gl={{ antialias: true, alpha: true }}
        dpr={[1, 2]}
      >
        <PerspectiveCamera makeDefault position={[0, 0, 5]} fov={50} />
        
        <ambientLight intensity={0.5} />
        <directionalLight
          position={[10, 10, 5]}
          intensity={1}
          castShadow
          shadow-mapSize-width={1024}
          shadow-mapSize-height={1024}
        />
        <directionalLight position={[-10, -10, -5]} intensity={0.3} />
        <pointLight position={[0, 5, 0]} intensity={0.5} />
        
        <Suspense fallback={<LoadingFallback />}>
          <Model url={modelUrl} dimensions={dimensions} />
          <Environment preset="studio" />
        </Suspense>
        
        <OrbitControls
          enablePan={true}
          enableZoom={true}
          enableRotate={true}
          minDistance={2}
          maxDistance={10}
          minPolarAngle={0}
          maxPolarAngle={Math.PI / 1.5}
        />
      </Canvas>
    </div>
  );
};

export default ModelViewer;
import React, { Suspense, useRef, useEffect, useState } from 'react';
import { Canvas, useFrame, useLoader } from '@react-three/fiber';
import { OrbitControls, Environment, PerspectiveCamera, Html, useProgress, Loader } from '@react-three/drei';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';
import * as THREE from 'three';
import { Interactive } from '@react-three/xr';

function Model({ url, dimensions, onModelLoaded }) {
  const gltf = useLoader(GLTFLoader, url);
  const meshRef = useRef();

  useEffect(() => {
    if (gltf && gltf.scene) {
      const box = new THREE.Box3().setFromObject(gltf.scene);
      const size = new THREE.Vector3();
      box.getSize(size);

      const center = new THREE.Vector3();
      box.getCenter(center);
      gltf.scene.position.sub(center);

      let scaleFactor = 1;

      if (dimensions && dimensions.diameter) {
        const maxModelDimension = Math.max(size.x, size.z);
        const targetSizeInMeters = dimensions.diameter / 100;

        if (maxModelDimension > 0) {
          scaleFactor = targetSizeInMeters / maxModelDimension;
        }
      }

      gltf.scene.scale.set(scaleFactor, scaleFactor, scaleFactor);

      if (onModelLoaded) {
        onModelLoaded(gltf.scene);
      }
    }
  }, [gltf, dimensions, onModelLoaded]);

  useFrame(() => {
    if (meshRef.current) {
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

// AR-specific component for placing the model
function ARModelPlacer({ model, onPlace }) {
  const [placed, setPlaced] = useState(false);

  return (
      <Interactive onSelect={() => {
        setPlaced(true);
        onPlace();
      }}>
        <primitive object={model} />
        {!placed && (
            <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.01, 0]}>
              <ringGeometry args={[0.1, 0.12, 64]} />
              <meshStandardMaterial color="white" emissive="white" />
            </mesh>
        )}
      </Interactive>
  );
}

const ModelViewer = ({ modelUrl, dimensions, className = '', onModelLoaded }) => {
  return (
      <>
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

            <Suspense fallback={null}>
              <Model url={modelUrl} dimensions={dimensions} onModelLoaded={onModelLoaded} />
              <Environment preset="studio" />
            </Suspense>

            <OrbitControls
                enablePan={true}
                enableZoom={true}
                enableRotate={true}
                minDistance={0.5}
                maxDistance={10}
                minPolarAngle={0}
                maxPolarAngle={Math.PI / 1.5}
            />
          </Canvas>
        </div>
        {/* Drei's Loader will automatically track suspense progress and display it */}
        <Loader
            containerStyles={{
              background: 'rgba(0,0,0,0.8)',
              width: '100%',
              height: '100%',
              position: 'absolute',
              top: 0,
              left: 0
            }}
            innerStyles={{
              backgroundColor: '#fff',
              width: '200px',
              height: '10px',
              borderRadius: '5px'
            }}
            barStyles={{
              backgroundColor: '#3b82f6', // blue-500
              height: '10px',
              borderRadius: '5px'
            }}
            dataStyles={{
              color: '#fff',
              position: 'absolute',
              top: '60%',
              fontSize: '16px'
            }}
        />
      </>
  );
};

// Deprecated, use Drei's Loader instead
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

export { ModelViewer, ARModelPlacer, LoadingFallback };
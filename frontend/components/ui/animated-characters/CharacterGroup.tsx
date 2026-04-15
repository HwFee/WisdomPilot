'use client'

import { useState, useEffect, useRef } from 'react'
import { Pupil } from './Pupil'
import { EyeBall } from './EyeBall'

interface CharacterGroupProps {
  isLookingAway?: boolean
  lang?: 'zh' | 'en'
}

export function CharacterGroup({ isLookingAway = false, lang = 'zh' }: CharacterGroupProps) {
  const [mouseX, setMouseX] = useState<number>(0)
  const [mouseY, setMouseY] = useState<number>(0)
  const [isPurpleBlinking, setIsPurpleBlinking] = useState(false)
  const [isBlackBlinking, setIsBlackBlinking] = useState(false)

  const purpleRef = useRef<HTMLDivElement>(null)
  const blackRef = useRef<HTMLDivElement>(null)
  const yellowRef = useRef<HTMLDivElement>(null)
  const orangeRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMouseX(e.clientX)
      setMouseY(e.clientY)
    }

    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])

  // Blinking effect for purple character
  useEffect(() => {
    const getRandomBlinkInterval = () => Math.random() * 4000 + 3000

    const scheduleBlink = () => {
      const blinkTimeout = setTimeout(() => {
        setIsPurpleBlinking(true)
        setTimeout(() => {
          setIsPurpleBlinking(false)
          scheduleBlink()
        }, 150)
      }, getRandomBlinkInterval())

      return blinkTimeout
    }

    const timeout = scheduleBlink()
    return () => clearTimeout(timeout)
  }, [])

  // Blinking effect for black character
  useEffect(() => {
    const getRandomBlinkInterval = () => Math.random() * 4000 + 3000

    const scheduleBlink = () => {
      const blinkTimeout = setTimeout(() => {
        setIsBlackBlinking(true)
        setTimeout(() => {
          setIsBlackBlinking(false)
          scheduleBlink()
        }, 150)
      }, getRandomBlinkInterval())

      return blinkTimeout
    }

    const timeout = scheduleBlink()
    return () => clearTimeout(timeout)
  }, [])

  const calculatePosition = (ref: React.RefObject<HTMLDivElement | null>) => {
    if (!ref.current) return { faceX: 0, faceY: 0, bodySkew: 0 }

    const rect = ref.current.getBoundingClientRect()
    const centerX = rect.left + rect.width / 2
    const centerY = rect.top + rect.height / 3

    const deltaX = mouseX - centerX
    const deltaY = mouseY - centerY

    const faceX = Math.max(-15, Math.min(15, deltaX / 20))
    const faceY = Math.max(-10, Math.min(10, deltaY / 30))
    const bodySkew = Math.max(-6, Math.min(6, -deltaX / 120))

    return { faceX, faceY, bodySkew }
  }

  const purplePos = calculatePosition(purpleRef)
  const blackPos = calculatePosition(blackRef)
  const yellowPos = calculatePosition(yellowRef)
  const orangePos = calculatePosition(orangeRef)

  return (
    <div className="relative" style={{ width: '550px', height: '400px' }}>
      {/* Purple tall rectangle character - Back layer */}
      <div
        ref={purpleRef}
        className="absolute bottom-0 transition-all duration-500 ease-out"
        style={{
          left: '70px',
          width: '180px',
          height: '400px',
          backgroundColor: '#6C3FF5',
          borderRadius: '10px 10px 0 0',
          zIndex: 1,
          transform: isLookingAway
            ? `translateX(-25px)`
            : `skewX(${purplePos.bodySkew || 0}deg)`,
          transformOrigin: 'bottom center',
        }}
      >
        <div
          className="absolute flex gap-8 transition-all duration-300"
          style={{
            left: `${45 + (isLookingAway ? -15 : purplePos.faceX)}px`,
            top: `${40 + (isLookingAway ? 5 : purplePos.faceY)}px`,
          }}
        >
          <EyeBall
            size={18}
            pupilSize={7}
            maxDistance={5}
            eyeColor="white"
            pupilColor="#2D2D2D"
            isBlinking={isPurpleBlinking}
            forceLookX={isLookingAway ? -8 : undefined}
            forceLookY={isLookingAway ? 2 : undefined}
          />
          <EyeBall
            size={18}
            pupilSize={7}
            maxDistance={5}
            eyeColor="white"
            pupilColor="#2D2D2D"
            isBlinking={isPurpleBlinking}
            forceLookX={isLookingAway ? -8 : undefined}
            forceLookY={isLookingAway ? 2 : undefined}
          />
        </div>
      </div>

      {/* Black tall rectangle character - Middle layer */}
      <div
        ref={blackRef}
        className="absolute bottom-0 transition-all duration-500 ease-out"
        style={{
          left: '240px',
          width: '120px',
          height: '310px',
          backgroundColor: '#2D2D2D',
          borderRadius: '8px 8px 0 0',
          zIndex: 2,
          transform: isLookingAway
            ? `translateX(-15px)`
            : `skewX(${blackPos.bodySkew || 0}deg)`,
          transformOrigin: 'bottom center',
        }}
      >
        <div
          className="absolute flex gap-6 transition-all duration-300"
          style={{
            left: `${26 + (isLookingAway ? -12 : blackPos.faceX)}px`,
            top: `${32 + (isLookingAway ? 4 : blackPos.faceY)}px`,
          }}
        >
          <EyeBall
            size={16}
            pupilSize={6}
            maxDistance={4}
            eyeColor="white"
            pupilColor="#2D2D2D"
            isBlinking={isBlackBlinking}
            forceLookX={isLookingAway ? -7 : undefined}
            forceLookY={isLookingAway ? 2 : undefined}
          />
          <EyeBall
            size={16}
            pupilSize={6}
            maxDistance={4}
            eyeColor="white"
            pupilColor="#2D2D2D"
            isBlinking={isBlackBlinking}
            forceLookX={isLookingAway ? -7 : undefined}
            forceLookY={isLookingAway ? 2 : undefined}
          />
        </div>
      </div>

      {/* Orange semi-circle character - Front left */}
      <div
        ref={orangeRef}
        className="absolute bottom-0 transition-all duration-500 ease-out"
        style={{
          left: '0px',
          width: '240px',
          height: '200px',
          zIndex: 3,
          backgroundColor: '#FF9B6B',
          borderRadius: '120px 120px 0 0',
          transform: isLookingAway
            ? `translateX(-10px)`
            : `skewX(${orangePos.bodySkew || 0}deg)`,
          transformOrigin: 'bottom center',
        }}
      >
        <div
          className="absolute flex gap-8 transition-all duration-300"
          style={{
            left: `${82 + (isLookingAway ? -20 : (orangePos.faceX || 0))}px`,
            top: `${90 + (isLookingAway ? 5 : (orangePos.faceY || 0))}px`,
          }}
        >
          <Pupil size={12} maxDistance={5} pupilColor="#2D2D2D" forceLookX={isLookingAway ? -8 : undefined} forceLookY={isLookingAway ? 2 : undefined} />
          <Pupil size={12} maxDistance={5} pupilColor="#2D2D2D" forceLookX={isLookingAway ? -8 : undefined} forceLookY={isLookingAway ? 2 : undefined} />
        </div>
      </div>

      {/* Yellow tall rectangle character - Front right */}
      <div
        ref={yellowRef}
        className="absolute bottom-0 transition-all duration-500 ease-out"
        style={{
          left: '310px',
          width: '140px',
          height: '230px',
          backgroundColor: '#E8D754',
          borderRadius: '70px 70px 0 0',
          zIndex: 4,
          transform: isLookingAway
            ? `translateX(-20px)`
            : `skewX(${yellowPos.bodySkew || 0}deg)`,
          transformOrigin: 'bottom center',
        }}
      >
        <div
          className="absolute flex gap-6 transition-all duration-300"
          style={{
            left: `${52 + (isLookingAway ? -18 : (yellowPos.faceX || 0))}px`,
            top: `${40 + (isLookingAway ? 5 : (yellowPos.faceY || 0))}px`,
          }}
        >
          <Pupil size={12} maxDistance={5} pupilColor="#2D2D2D" forceLookX={isLookingAway ? -8 : undefined} forceLookY={isLookingAway ? 2 : undefined} />
          <Pupil size={12} maxDistance={5} pupilColor="#2D2D2D" forceLookX={isLookingAway ? -8 : undefined} forceLookY={isLookingAway ? 2 : undefined} />
        </div>
        <div
          className="absolute w-20 h-[4px] bg-[#2D2D2D] rounded-full transition-all duration-300"
          style={{
            left: `${40 + (isLookingAway ? -15 : (yellowPos.faceX || 0))}px`,
            top: `${88 + (isLookingAway ? 5 : (yellowPos.faceY || 0))}px`,
          }}
        />
      </div>
    </div>
  )
}

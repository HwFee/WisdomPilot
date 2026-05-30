'use client'

import { useState, useEffect, useRef } from 'react'
import { Pupil } from './Pupil'
import { EyeBall } from './EyeBall'

interface CharacterGroupProps {
  isLookingAway?: boolean
  lang?: 'zh' | 'en'
}

export function CharacterGroup({ isLookingAway = false, lang = 'zh' }: CharacterGroupProps) {
  const [mousePos, setMousePos] = useState<{ x: number; y: number }>({ x: 0, y: 0 })
  const [blinkState, setBlinkState] = useState<{ purple: boolean; black: boolean }>({ purple: false, black: false })
  const mouseX = mousePos.x
  const mouseY = mousePos.y

  const purpleRef = useRef<HTMLDivElement>(null)
  const blackRef = useRef<HTMLDivElement>(null)
  const yellowRef = useRef<HTMLDivElement>(null)
  const orangeRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePos({ x: e.clientX, y: e.clientY })
    }

    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])

  // Blinking effect for both characters
  useEffect(() => {
    const timeouts: ReturnType<typeof setTimeout>[] = []

    const queueBlink = (char: 'purple' | 'black', on: boolean, delay: number) => {
      const t = setTimeout(() => {
        setBlinkState(prev => ({ ...prev, [char]: on }))
        if (on) {
          queueBlink(char, false, 150)
        } else {
          queueBlink(char, true, Math.random() * 4000 + 3000)
        }
      }, delay)
      timeouts.push(t)
    }

    queueBlink('purple', true, 3000)
    queueBlink('black', true, 3500)

    return () => {
      for (const id of timeouts) {
        clearTimeout(id)
      }
    }
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
    <div className="relative w-[550px] h-[400px]">
      {/* Purple tall rectangle character - Back layer */}
      <div
        ref={purpleRef}
        className="absolute bottom-0 transition-all duration-500 ease-out left-[70px] w-[180px] h-[400px] bg-[#6C3FF5] rounded-t-[10px] z-[1] origin-bottom"
        style={{
          transform: isLookingAway
            ? `translateX(-25px)`
            : `skewX(${purplePos.bodySkew || 0}deg)`,
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
            isBlinking={blinkState.purple}
            forceLookX={isLookingAway ? -8 : undefined}
            forceLookY={isLookingAway ? 2 : undefined}
          />
          <EyeBall
            size={18}
            pupilSize={7}
            maxDistance={5}
            eyeColor="white"
            pupilColor="#2D2D2D"
            isBlinking={blinkState.purple}
            forceLookX={isLookingAway ? -8 : undefined}
            forceLookY={isLookingAway ? 2 : undefined}
          />
        </div>
      </div>

      {/* Black tall rectangle character - Middle layer */}
      <div
        ref={blackRef}
        className="absolute bottom-0 transition-all duration-500 ease-out left-[240px] w-[120px] h-[310px] bg-[#2D2D2D] rounded-t-[8px] z-[2] origin-bottom"
        style={{
          transform: isLookingAway
            ? `translateX(-15px)`
            : `skewX(${blackPos.bodySkew || 0}deg)`,
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
            isBlinking={blinkState.black}
            forceLookX={isLookingAway ? -7 : undefined}
            forceLookY={isLookingAway ? 2 : undefined}
          />
          <EyeBall
            size={16}
            pupilSize={6}
            maxDistance={4}
            eyeColor="white"
            pupilColor="#2D2D2D"
            isBlinking={blinkState.black}
            forceLookX={isLookingAway ? -7 : undefined}
            forceLookY={isLookingAway ? 2 : undefined}
          />
        </div>
      </div>

      {/* Orange semi-circle character - Front left */}
      <div
        ref={orangeRef}
        className="absolute bottom-0 transition-all duration-500 ease-out left-0 w-[240px] h-[200px] z-[3] bg-[#FF9B6B] rounded-t-[120px] origin-bottom"
        style={{
          transform: isLookingAway
            ? `translateX(-10px)`
            : `skewX(${orangePos.bodySkew || 0}deg)`,
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
        className="absolute bottom-0 transition-all duration-500 ease-out left-[310px] w-[140px] h-[230px] bg-[#E8D754] rounded-t-[70px] z-[4] origin-bottom"
        style={{
          transform: isLookingAway
            ? `translateX(-20px)`
            : `skewX(${yellowPos.bodySkew || 0}deg)`,
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

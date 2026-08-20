import React, { useEffect, useRef, useState } from 'react';

interface ScrollRevealProps {
  children: React.ReactNode;
  className?: string;
  delay?: number;
  direction?: 'up' | 'down' | 'left' | 'right' | 'none';
}

export const ScrollReveal: React.FC<ScrollRevealProps> = ({
  children,
  className = '',
  delay = 0,
  direction = 'up',
}) => {
  const ref = useRef<HTMLDivElement | null>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (typeof IntersectionObserver === 'undefined') {
      setIsVisible(true);
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.unobserve(entry.target);
        }
      },
      {
        threshold: 0.1,
        rootMargin: '0px 0px -30px 0px',
      }
    );

    const current = ref.current;
    if (current) {
      observer.observe(current);
    }

    return () => {
      if (current) observer.unobserve(current);
    };
  }, []);

  const getTransform = () => {
    if (!isVisible) {
      switch (direction) {
        case 'up':
          return 'translateY(28px)';
        case 'down':
          return 'translateY(-28px)';
        case 'left':
          return 'translateX(28px)';
        case 'right':
          return 'translateX(-28px)';
        case 'none':
          return 'none';
      }
    }
    return 'none';
  };

  return (
    <div
      ref={ref}
      className={`${className} transition-all duration-700 ease-[cubic-bezier(0.16,1,0.3,1)]`}
      style={{
        opacity: isVisible ? 1 : 0,
        transform: getTransform(),
        transitionDelay: `${delay}ms`,
        willChange: 'opacity, transform',
      }}
    >
      {children}
    </div>
  );
};

interface TextScrollRevealProps {
  text: string;
  className?: string;
  highlightWords?: string[];
  highlightClass?: string;
}

export const TextScrollReveal: React.FC<TextScrollRevealProps> = ({
  text,
  className = '',
  highlightWords = [],
  highlightClass = 'text-[#536DFE] font-medium',
}) => {
  const ref = useRef<HTMLParagraphElement | null>(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    if (typeof IntersectionObserver === 'undefined') {
      setInView(true);
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true);
        }
      },
      { threshold: 0.15, rootMargin: '0px 0px -30px 0px' }
    );

    const current = ref.current;
    if (current) observer.observe(current);

    return () => {
      if (current) observer.unobserve(current);
    };
  }, []);

  const words = text.split(' ');

  return (
    <p ref={ref} className={`${className} leading-relaxed`}>
      {words.map((word, idx) => {
        const cleanWord = word.replace(/[^a-zA-Zа-яА-Я0-9]/g, '');
        const isHighlighted = highlightWords.some(
          (hw) => hw.toLowerCase() === cleanWord.toLowerCase()
        );

        return (
          <span
            key={idx}
            className={`inline-block transition-all duration-500 mr-[0.25em] ${
              isHighlighted ? highlightClass : ''
            }`}
            style={{
              opacity: inView ? 1 : 0.25,
              transform: inView ? 'translateY(0px)' : 'translateY(6px)',
              transitionDelay: `${Math.min(idx * 20, 600)}ms`,
            }}
          >
            {word}
          </span>
        );
      })}
    </p>
  );
};

'use client'

import React, { useState } from 'react';
import styles from './GooeyButton.module.css';
import { usePathname } from 'next/navigation';

interface GooeyButtonProps {
  icon: React.ReactNode;
  title: string;
  href: string;
}

export const GooeyButton: React.FC<GooeyButtonProps> = ({ icon, title, href }) => {
  const pathname = usePathname();
  const isActive = pathname === href;
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div 
      className={styles['gooey-button-container']}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <button 
        className={`${styles['gooey-button']} ${isActive ? styles['active'] : ''} ${isHovered ? styles['hovered'] : ''}`} 
        title={title}
      >
        <div className={styles['icon-wrapper']}>
          {React.cloneElement(icon as React.ReactElement, { 
            className: styles['icon']
          })}
        </div>
        <div className={styles['gooey-blob']}></div>
      </button>
      <span className={`${styles['gooey-text']} ${(isHovered && !isActive) ? styles['visible'] : ''}`}>
        {title}
      </span>
    </div>
  );
};

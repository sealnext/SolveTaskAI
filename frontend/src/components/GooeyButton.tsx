'use client'

import React, { useState, useRef, useImperativeHandle, forwardRef, useEffect } from 'react';
import { useHotkeys } from 'react-hotkeys-hook';
import styles from './GooeyButton.module.css';
import { usePathname } from 'next/navigation';

interface GooeyButtonProps {
  icon: React.ReactNode;
  title: string;
  href: string;
  shortcutKey?: string;
  onClick?: (event: React.MouseEvent) => void;
}

const isMac = typeof window !== 'undefined' && navigator.platform.toUpperCase().indexOf('MAC') >= 0;

const modifierKeyToIcon: { [key: string]: string } = {
  alt: isMac ? '⌥' : 'Alt',
  ctrl: isMac ? '⌃' : 'Ctrl',
  meta: isMac ? '⌘' : 'Win',
  shift: isMac ? '⇧' : 'Shift',
};

const formatShortcut = (shortcut: string): React.ReactNode[] => {
  return shortcut.split('+').map((key, index) => (
    <span key={index} className={styles['shortcut-key']}>
      {modifierKeyToIcon[key.toLowerCase()] || key.toUpperCase()}
    </span>
  ));
};

export const GooeyButton = forwardRef<HTMLButtonElement, GooeyButtonProps>(
  ({ icon, title, href, shortcutKey, onClick }, ref) => {
    const pathname = usePathname();
    const isActive = pathname === href;
    const [isHovered, setIsHovered] = useState(false);
    const innerRef = useRef<HTMLButtonElement>(null);
    const [formattedShortcut, setFormattedShortcut] = useState('');

    useImperativeHandle(ref, () => innerRef.current!);

    useEffect(() => {
      if (shortcutKey) {
        setFormattedShortcut(formatShortcut(shortcutKey));
      }
    }, [shortcutKey]);

    useHotkeys(shortcutKey || '', (event) => {
      event.preventDefault();
      innerRef.current?.click();
    }, { enableOnFormTags: true }, []);

    return (
      <div 
        className={styles['gooey-button-container']}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        onClick={onClick}
      >
        <button 
          ref={innerRef}
          className={`${styles['gooey-button']} ${isActive ? styles['active'] : ''} ${isHovered ? styles['hovered'] : ''}`} 
          title={title}
        >
          <div className={styles['icon-wrapper']}>
            {React.cloneElement(icon as React.ReactElement, { 
              className: `${styles['icon']} text-muted-foreground`
            })}
          </div>
          <div className={`${styles['gooey-blob']} bg-accent`}></div>
        </button>
        <span className={`${styles['gooey-text']} ${(isHovered && !isActive) ? styles['visible'] : ''}`}>
          {title} 
          {formattedShortcut && (
            <span className={styles['shortcut-container']}>
              {formattedShortcut}
            </span>
          )}
        </span>
      </div>
    );
  }
);

GooeyButton.displayName = 'GooeyButton';

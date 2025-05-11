import { atomWithStorage } from 'jotai/utils';

const themeAtom = atomWithStorage('theme', 'system');

export { themeAtom };

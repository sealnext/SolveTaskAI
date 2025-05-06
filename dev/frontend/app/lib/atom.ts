import { atomWithStorage } from 'jotai/utils';

const themeAtom = atomWithStorage('theme', 'system');
const userNameAtom = atomWithStorage<string | null>('name', null);
const userEmailAtom = atomWithStorage<string | null>('email', null);
const userIsEmailVerifiedAtom = atomWithStorage<boolean>('isEmailVerified', false);

export { themeAtom, userNameAtom, userEmailAtom, userIsEmailVerifiedAtom };

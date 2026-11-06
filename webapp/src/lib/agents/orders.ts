import type { Settings } from "../types";

/** Smallest 40ft container load (tonnes), krakacoal.com MOQ. */
export const T_PER_40FT = 25;

/** Large order rule: at least `largeOrderContainers40ft` containers of 40ft (N x 25 t). Large orders need a second, explicit confirmation by the owner. */
export function isLargeOrder(qtyT: number, s: Settings): boolean {
  return qtyT >= s.largeOrderContainers40ft * T_PER_40FT - 1e-9;
}

export const largeOrderNote = (s: Settings) =>
  `LARGE ORDER (at least ${s.largeOrderContainers40ft} x 40ft = ${s.largeOrderContainers40ft * T_PER_40FT} t): before approving, check buyer credit and references, supplier capacity for the month, and the down payment.`;

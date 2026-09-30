import type { Product, Settings } from "../types";
import { floorFob } from "./quote";

export interface Move { decision: "accept" | "counter" | "hold" | "decline"; offerFobUsdT: number; message: string; floor: number; room: number }

/** Capped concession ladder: hold at list first, then give at most a third of the allowed room per round, never below the floor. */
export function negotiate(p: Product, s: Settings, counterFob: number, round: number, listFob = p.listPriceUsdT): Move {
  const floor = floorFob(p, s, listFob);
  const room = Math.max(0, listFob - floor);
  const step = (r: number) => Math.round(listFob - room * Math.min(1, Math.max(0, (r - 1) / 3)));
  if (counterFob >= listFob) return { decision: "accept", offerFobUsdT: counterFob, message: `Accept USD ${counterFob} FOB: at or above your list price.`, floor, room };
  if (counterFob >= floor && counterFob >= step(round)) return { decision: "accept", offerFobUsdT: counterFob, message: `Accept USD ${counterFob} FOB: within your cap (floor ${floor}).`, floor, room };
  if (counterFob < p.supplierPriceUsdT) return { decision: "decline", offerFobUsdT: floor, message: `Decline: USD ${counterFob} is below your supplier cost (USD ${p.supplierPriceUsdT}). Restate USD ${listFob} or the floor ${floor} as final.`, floor, room };
  const next = step(round + 1 > 4 ? 4 : round + 1);
  const final = next <= floor;
  return {
    decision: round <= 1 ? "hold" : "counter", offerFobUsdT: round <= 1 ? listFob : Math.max(floor, next),
    message: round <= 1 ? `Hold at list USD ${listFob} FOB. Say the price reflects lab-verified quality and current supplier cost; offer alternatives (a lower grade, a larger volume) before price.` : `Counter at USD ${Math.max(floor, next)} FOB${final ? " and state it as your final price" : ""}. Total room you have is only USD ${room}/t (${(100 * room / listFob).toFixed(1)}% of list).`,
    floor, room,
  };
}

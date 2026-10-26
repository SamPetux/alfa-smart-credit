import { describe, expect, it } from "vitest";
import { formatAmount, formatMoney, formatRate, moneyToInput, parseMoneyInput, toKopecks } from "./money";

const NBSP = " ";

describe("money", () => {
  it("formats money strings without floating point", () => {
    expect(formatMoney("641000.00")).toBe(`641${NBSP}000,00${NBSP}₽`);
    expect(formatMoney("59994.5")).toBe(`59${NBSP}994,50${NBSP}₽`);
    expect(formatMoney("9007199254740993.01")).toBe(
      `9${NBSP}007${NBSP}199${NBSP}254${NBSP}740${NBSP}993,01${NBSP}₽`,
    );
  });

  it("prints a real zero and a dash for missing", () => {
    expect(formatMoney("0.00")).toBe(`0,00${NBSP}₽`);
    expect(formatMoney(null)).toBe("—");
    expect(formatMoney(undefined)).toBe("—");
  });

  it("drops zero kopecks for loan amounts", () => {
    expect(formatAmount("1000000.00")).toBe(`1${NBSP}000${NBSP}000${NBSP}₽`);
    expect(formatAmount("1000.50")).toBe(`1${NBSP}000,50${NBSP}₽`);
  });

  it("formats rates by shifting the decimal string", () => {
    expect(formatRate("0.22")).toBe(`22${NBSP}%`);
    expect(formatRate("0.225")).toBe(`22,5${NBSP}%`);
    expect(formatRate("0.05")).toBe(`5${NBSP}%`);
    expect(formatRate(null)).toBe("—");
  });

  it("parses user input into canonical money strings", () => {
    expect(parseMoneyInput("1 000 000")).toBe("1000000.00");
    expect(parseMoneyInput("1000,5")).toBe("1000.50");
    expect(parseMoneyInput("0")).toBe("0.00");
    expect(parseMoneyInput("")).toBeNull();
    expect(parseMoneyInput("12abc")).toBeNull();
    expect(parseMoneyInput("1.234")).toBeNull();
    expect(parseMoneyInput("-5")).toBeNull();
  });

  it("compares bounds in kopecks and round-trips the input view", () => {
    expect(toKopecks("100000.00") < toKopecks("100000.01")).toBe(true);
    expect(moneyToInput("1000000.00")).toBe(`1${NBSP}000${NBSP}000`);
    expect(moneyToInput("1000.50")).toBe(`1${NBSP}000,50`);
  });
});

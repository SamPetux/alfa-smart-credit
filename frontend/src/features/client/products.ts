import { useQuery } from "@tanstack/react-query";
import { api } from "../../api/endpoints";
import { queryKeys } from "../../api/queryClient";
import type { Product, ProductCode } from "../../api/types";

export function useProducts() {
  return useQuery({
    queryKey: queryKeys.products,
    queryFn: ({ signal }) => api.products({ signal }),
    staleTime: 5 * 60_000,
  });
}

/** Название продукта из каталога API; код — запасной вариант, пока каталог грузится. */
export function productTitle(products: Product[] | undefined, code: ProductCode | null | undefined): string {
  if (!code) return "Продукт не выбран";
  return products?.find((product) => product.code === code)?.title ?? code;
}

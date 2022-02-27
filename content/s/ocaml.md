+++
title = "🐫 OCaml"
slug = "ocaml"
+++

#### Tail recursive calls

How can one verify that a function application is tail-recusive in ocaml at compile time?

Simply add the `[@tailcall]` on a function application to check that it is tail recursive. (Available since OCaml version 4.03).

```ocaml
let rec fibo = function
  | 0 -> 0  
  | 1 -> 1  
  | n -> fibo (n - 1)  + fibo (n - 2)

let () = (fibo[@tailcall]) 8 |> Printf.printf "fibo 8 = %d\n" 
```

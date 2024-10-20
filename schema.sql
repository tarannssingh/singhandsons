create table
  public.cart (
    id bigint generated by default as identity not null,
    created_at timestamp with time zone not null default now(),
    constraint cart_pkey primary key (id),
    constraint cart_id_key unique (id)
  ) tablespace pg_default;

create table
  public.cart_item (
    id bigint generated by default as identity not null,
    created_at timestamp with time zone not null default now(),
    cart_id bigint not null,
    bottle_id bigint not null,
    quantity integer not null,
    constraint cart_item_pkey primary key (id),
    constraint cart_item_bottle_id_fkey foreign key (bottle_id) references potion_inventory (id),
    constraint cart_item_cart_id_fkey foreign key (cart_id) references cart (id)
  ) tablespace pg_default;

create unique index if not exists cart_item_potion on public.cart_item using btree (cart_id, bottle_id) tablespace pg_default;


create table
  public.global_inventory (
    id bigint generated by default as identity not null,
    created_at timestamp with time zone not null default now(),
    num_green_ml integer not null default 0,
    gold integer not null default 100,
    potion_capacity integer not null default 1,
    ml_capacity integer not null default 1,
    num_red_ml integer not null default 0,
    num_blue_ml integer not null default 0,
    num_dark_ml integer not null default 0,
    constraint global_inventory_pkey primary key (id)
  ) tablespace pg_default;

  create table global_inv



  create table
  public.global_inventory (
    id bigint generated by default as identity not null,
    created_at timestamp with time zone not null default now(),
    num_green_ml integer not null default 0,
    gold integer not null default 100,
    potion_capacity integer not null default 1,
    ml_capacity integer not null default 1,
    num_red_ml integer not null default 0,
    num_blue_ml integer not null default 0,
    num_dark_ml integer not null default 0,
    constraint global_inventory_pkey primary key (id)
  ) tablespace pg_default;

  create table
  public.potion_inventory (
    id bigint generated by default as identity not null,
    created_at timestamp with time zone not null default now(),
    sku character varying not null,
    num_potions integer not null default 0,
    num_price integer not null default 50,
    green integer not null default 0,
    red integer not null default 0,
    blue integer not null default 0,
    dark integer not null default 0,
    name character varying not null default 'Potion'::character varying,
    to_sell integer not null default 1,
    constraint potion_inventory_pkey primary key (id)
  ) tablespace pg_default;
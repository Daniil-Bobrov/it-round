create table users (
id integer primary key autoincrement,
deductions text not null
);
create table deductions (
id integer primary key autoincrement,
fields text not null,
deduction text not null,
type text not null,
time text not null
);
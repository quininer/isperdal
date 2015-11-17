use isperdal::{ Node };

// In a parallel universe, isperdal is written with Rust.
fn main() {
    "/".all(Box::new(|this, req, res| {
        res.push("Hello world.").ok()
    })).run();
}

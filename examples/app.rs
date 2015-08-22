use isperdal::{Microwave};

// In a parallel universe, isperdal is written with Rust.
fn main() {
    "/".all("", box |this, req, res| {
        res.ok("Hello world.");
    }).run();
}

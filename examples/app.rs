use isperdal::{Microwave};

fn main() {
    "/".all("", box |this, req, res| {
        res.ok("Hello world.");
    }).run();
}

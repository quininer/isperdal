use isperdal::{Microwave};

fn main() {
    "/".all("", box |this, req, res| {
        res.push("Hello world.");
    }).run();
}
